# -*- coding: utf-8 -*-
"""S13-PUSH 反汇编核心库（自建，不 import 任何其它卡的 work 代码）。
加载 gamemd.exe(PE) + function_atlas + coverage，提供：
 - read_va / disasm_body / disasm_range
 - 通道A ③b② 机械预筛：call -> test/or/cmp eax -> jcc，taken/fallthrough 动作签名不同，
   可伪证返回约定（call-site sentinel 或 callee return profile）。
 - 通道B ③b① 跳转表机械预筛：jcc 边界 + `jmp dword [reg*4 + disp]` 间接跳表 + 逐项目标。
 - RTTI / 虚表 / 构造安装点 / direct caller 辅助。
所有地址用 int VA；输出 entry 列一律 "%08X"（大写、无 0x）。
"""
import csv, json, os, re, pefile
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE   = os.path.join(BASE, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
COV   = os.path.join(BASE, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")

def hx(x):
    return "%08X" % (x & 0xFFFFFFFF)

def norm(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

# ---------- singleton PE ----------
_pe = pefile.PE(EXE)
IB = _pe.OPTIONAL_HEADER.ImageBase
_text_sec = next(s for s in _pe.sections if s.Name.rstrip(b"\x00") == b".text")
TEXT_VA = IB + _text_sec.VirtualAddress
TEXT_DATA = _text_sec.get_data()
# 卡片口径：.text = [0x401000, 0x7E038D)，用 VirtualSize（=0x3DF38D），不是 raw size。
TEXT_SIZE = _text_sec.Misc_VirtualSize
_rdata_sec = next((s for s in _pe.sections if s.Name.rstrip(b"\x00") == b".rdata"), None)
RDATA_VA = IB + _rdata_sec.VirtualAddress if _rdata_sec else 0
RDATA_DATA = _rdata_sec.get_data() if _rdata_sec else b""
RDATA_SIZE = max(_rdata_sec.Misc_VirtualSize, _rdata_sec.SizeOfRawData) if _rdata_sec else 0

def section_for(va):
    for s in _pe.sections:
        v = IB + s.VirtualAddress
        # 用 VirtualSize 作为段逻辑边界（与卡片 .text=[0x401000,0x7E038D) 一致）
        if v <= va < v + s.Misc_VirtualSize:
            return s
    return None

def read_va(va, maxlen):
    s = section_for(va)
    if not s:
        return b""
    off = va - (IB + s.VirtualAddress)
    data = s.get_data()
    if off < 0 or off >= len(data):
        return b""
    return data[off:off + maxlen]

def u32(va):
    b = read_va(va, 4)
    return int.from_bytes(b, "little") if len(b) == 4 else None

def in_text(va):
    return TEXT_VA <= va < TEXT_VA + TEXT_SIZE

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def disasm(va, data):
    return list(_md.disasm(data, va)) if data else []

def disasm_body(va, size):
    return disasm(va, read_va(va, size if size else 512))

# ---------- atlas / coverage ----------
def load_atlas():
    a = {}
    with open(ATLAS, encoding="utf-8-sig") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if not row or not row[0].strip():
                continue
            try:
                a[norm(row[0])] = dict(size=int(row[1]), n_instr=int(row[2]),
                                       n_callers=int(row[3]) if len(row) > 3 else None,
                                       n_callees=int(row[4]) if len(row) > 4 else None)
            except (ValueError, IndexError):
                pass
    return a

ATLAS = load_atlas()

def is_eax(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX

JCC_IDS = set()
for _cn in dir():
    if _cn.startswith("X86_INS_J") and _cn != "X86_INS_JMP":
        JCC_IDS.add(globals()[_cn])
for _cn in ("X86_INS_JE", "X86_INS_JNE", "X86_INS_JL", "X86_INS_JGE",
            "X86_INS_JLE", "X86_INS_JG", "X86_INS_JA", "X86_INS_JAE",
            "X86_INS_JB", "X86_INS_JBE", "X86_INS_JS", "X86_INS_JNS",
            "X86_INS_JO", "X86_INS_JNO", "X86_INS_JP", "X86_INS_JNP"):
    if _cn in globals():
        JCC_IDS.add(globals()[_cn])

def test_kind(ins):
    if ins.id == X86_INS_TEST and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
        return ("TEST_EAX", 0)
    if ins.id == X86_INS_OR and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
        return ("OR_EAX", 0)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2 and is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM:
        return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None

def is_falsifiable(v):
    if v in (0, 1, 0xFFFFFFFF):
        return True
    if 0x80000000 <= v <= 0x8FFFFFFF:
        return True
    if 0xC0000000 <= v <= 0xDFFFFFFF:
        return True
    return False

def path_sig(insns, start_idx, maxn=16):
    calls, rets = set(), set()
    has_ret = False
    eax = None
    end_eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a) and is_eax(b):
                eax = 0
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a):
                eax = (b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else None
        elif ins.id == X86_INS_RET:
            has_ret = True
            if eax is not None:
                rets.add(eax)
            end_eax = eax
            break
        elif ins.id == X86_INS_JMP:
            end_eax = eax
            break
        else:
            end_eax = eax
    return {"calls": sorted(calls), "rets": sorted(rets), "has_ret": has_ret, "end_eax": end_eax}

def callee_return_profile(callee_va):
    """(consts, n_rets, origins) if callee in .text with atlas boundary, else None."""
    if callee_va is None or not in_text(callee_va):
        return None
    key = hx(callee_va)
    cap = ATLAS.get(key, {}).get("size")
    if cap is None:
        return None
    code = read_va(callee_va, cap)
    if not code:
        return None
    insns = disasm(callee_va, code)
    consts, origins = set(), set()
    rets = 0
    eax = ("unknown",)
    for ins in insns:
        if ins.id == 0:
            continue
        if ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a) and is_eax(b):
                eax = ("imm", 0)
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a):
                eax = ("imm", b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else ("unknown",)
        elif ins.id == X86_INS_CALL:
            eax = ("call",)
        elif ins.id == X86_INS_RET:
            rets += 1
            origins.add(tuple(eax))
            if eax[0] == "imm":
                consts.add(eax[1])
            eax = ("unknown",)
        if ins.address - callee_va >= cap:
            break
    return {"consts": consts, "n_rets": rets, "origins": origins}

# ---------- Channel A: ③b② ----------
def channel_screen_A(insns):
    """Return list of P3 sites (defensible ③b② candidates) with P1/P2 provenance."""
    idx = {ins.address: i for i, ins in enumerate(insns)}
    p1 = p2 = p3 = 0
    sites = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        callee = None
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
        found = False
        for k in range(i + 1, min(i + 5, len(insns))):
            tk = test_kind(insns[k])
            if not tk:
                continue
            for m in range(k + 1, min(k + 3, len(insns))):
                jc = insns[m]
                if jc.id not in JCC_IDS:
                    continue
                p1 += 1
                tgt = jc.operands[0].imm if jc.operands and jc.operands[0].type == X86_OP_IMM else None
                ti = idx.get(tgt)
                sig_t = path_sig(insns, ti) if ti is not None else {"calls": [], "rets": [], "has_ret": False, "end_eax": "OUT_OF_BODY"}
                sig_f = path_sig(insns, m + 1)
                key = ("calls", "rets", "has_ret", "end_eax")
                if tuple(sig_t[x] for x in key) == tuple(sig_f[x] for x in key):
                    continue  # P2 fail: actions not genuinely different
                p2 += 1
                falsy = None
                if tk[0] == "CMP_IMM" and tk[1] is not None and is_falsifiable(tk[1]):
                    falsy = tk[1]
                elif tk[0] in ("TEST_EAX", "OR_EAX") and jc.id == X86_INS_JE:
                    falsy = 0
                prof = callee_return_profile(callee)
                prof_ok = bool(prof and any(is_falsifiable(v) for v in prof["consts"]) and len(prof["origins"]) >= 2)
                if falsy is None and not prof_ok:
                    continue  # P3 fail: no falsifiable return convention
                sites.append({
                    "call_addr": ins.address, "callee": callee,
                    "test_addr": insns[k].address, "test_kind": tk[0], "test_imm": tk[1],
                    "jcc_addr": jc.address, "jcc_mnemonic": jc.mnemonic, "jcc_target": tgt,
                    "fallthrough": jc.address + jc.size,
                    "sig_taken": sig_t, "sig_fallthrough": sig_f,
                    "p3_form": "call_site_cmp" if falsy is not None else "callee_profile",
                    "call_site_falsy": hex(falsy) if falsy is not None else None,
                    "callee_profile": {
                        "falsifiable_consts": [hex(v) for v in sorted(prof["consts"]) if is_falsifiable(v)] if prof else [],
                        "all_consts": [hex(v) for v in sorted(prof["consts"])] if prof else [],
                        "n_rets": prof["n_rets"] if prof else None,
                        "origins": [list(o) for o in prof["origins"]] if prof else [],
                        "callee_key": hx(callee) if callee else None,
                    },
                })
                p3 += 1
                found = True
                break
            if found:
                break
    return {"p1": p1, "p2": p2, "p3": p3, "sites": sites}

# ---------- Channel B: ③b① 跳转表 ----------
def channel_screen_B(insns):
    """Detect switch jump tables: `jmp dword ptr [reg*4 + disp]` (FF 24 8x) with a
    bounds cmp/ja before it and a base register; report each case target (per-path verifiable).
    Also accept the pattern `jmp dword ptr [reg + eax*4]` variants."""
    tables = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_JMP:
            continue
        if not ins.operands or ins.operands[0].type != X86_OP_MEM:
            continue
        op = ins.operands[0].mem
        # scale==4 and index != invalid -> scaled indirect jump table
        if op.scale != 4 or op.index in (X86_REG_INVALID, 0):
            continue
        # base register or disp present
        targets = []
        disp = op.disp
        base = op.base
        # bounds check: search backwards <=12 insns for cmp <index>,imm or ja/jbe
        bound = None
        for j in range(i - 1, max(-1, i - 14), -1):
            p = insns[j]
            if p.id == X86_INS_CMP and len(p.operands) == 2 and p.operands[1].type == X86_OP_IMM:
                bound = p.operands[1].imm & 0xFFFFFFFF
                break
        # resolve table base: disp (imm) is the table address when base is invalid
        table_va = None
        if base in (X86_REG_INVALID, 0) and disp:
            table_va = disp & 0xFFFFFFFF
        # if base register loaded from imm earlier, try to resolve
        if table_va is None:
            for j in range(i - 1, max(-1, i - 14), -1):
                p = insns[j]
                if p.id == X86_INS_MOV and len(p.operands) == 2 and p.operands[0].type == X86_OP_REG \
                   and p.operands[0].reg == base and p.operands[1].type == X86_OP_IMM:
                    table_va = (p.operands[1].imm & 0xFFFFFFFF) + (disp or 0)
                    break
        ncase = None
        if bound is not None:
            ncase = bound + 1
        # 跳表可在 .rdata 或 .text：只要求 4 字节可读（u32 非 None），目标须在 .text
        if table_va and ncase and 1 <= ncase <= 256:
            for c in range(ncase):
                t = u32(table_va + c * 4)
                if t is not None and in_text(t):
                    targets.append({"case": c, "target": t, "slot_va": table_va + c * 4})
        tables.append({
            "jmp_addr": ins.address, "mnemonic": ins.mnemonic, "op_str": ins.op_str,
            "index_reg": ins.reg_name(op.index) if op.index else None,
            "base_reg": ins.reg_name(base) if base else None,
            "disp": disp, "table_va": table_va, "bound": bound, "ncase": ncase,
            "targets": targets,
        })
    return tables

if __name__ == "__main__":
    print("RE core OK. text=[%08X,%08X) size=%d  rdata=%08X" % (TEXT_VA, TEXT_VA + TEXT_SIZE, TEXT_SIZE, RDATA_VA))
    print("atlas entries=%d" % len(ATLAS))
    # self-check: known positive channel A site (006E3DB0 from S15 delta, call 0x410380)
    ins = disasm_body(0x006E3DB0, 125)
    r = channel_screen_A(ins)
    print("self-check 006E3DB0 channelA P1=%d P2=%d P3=%d (expect >=1)" % (r["p1"], r["p2"], r["p3"]))
