# -*- coding: utf-8 -*-
"""S20-B1 反汇编底座（自建）。

提供：
 - PE 段表（含 raw data，按 VA 查）/ read_va / u32 / read_cstr
 - atlas 函数边界
 - disasm（capstone 5.0.7，skipdata=True）
 - ② 通道：entry 作 4B VA 的全镜像引用 → 槽 VA；回扫 [vt-4]=COL(sig==0) → [COL+0xC]=TD → TD+8 名串
 - ④ 通道：.text 中把 vt 作 imm32 写入 [mem] 的站点（C7 05 disp32 / C7 modrm），
             连带所在函数、是否 `push <f>; call 0x7C978A` 的 atexit 析构器、是否落在本行体内
 - ③b② 机械站点：call → test/or/cmp eax → jcc，两路动作签名不同
地址一律 int VA；对外 hex 用 "%08X"。
"""
import bisect
import csv
import os
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (
    X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
    X86_REG_EAX, X86_INS_CALL, X86_INS_JMP, X86_INS_RET,
    X86_INS_TEST, X86_INS_OR, X86_INS_CMP, X86_INS_MOV,
    X86_INS_XOR, X86_INS_SUB,
)

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
ATLAS_TSV = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
ATEXIT_VA = 0x7C978A


def hx(x):
    return "%08X" % (x & 0xFFFFFFFF)


# ---------------- PE ----------------
_pe = pefile.PE(EXE)
IB = _pe.OPTIONAL_HEADER.ImageBase

SECS = []  # (name, va_start, size, data)
for _s in _pe.sections:
    _nm = _s.Name.rstrip(b"\x00").decode("latin1")
    _va = IB + _s.VirtualAddress
    _sz = max(_s.Misc_VirtualSize, _s.SizeOfRawData)
    SECS.append((_nm, _va, _sz, _s.get_data()[: _sz] if _s.SizeOfRawData else b""))

_text = next(s for s in SECS if s[0] == ".text")
TEXT_VA, TEXT_SIZE, TEXT_DATA = _text[1], _text[2], _text[3]
# 卡片口径：.text = [0x401000, 0x7E038D) —— 用 VirtualSize，不是 raw size。
TEXT_VSIZE = next(s for s in _pe.sections if s.Name.rstrip(b"\x00") == b".text").Misc_VirtualSize
TEXT_END = TEXT_VA + TEXT_VSIZE


def sec_of(va):
    for nm, v0, sz, _d in SECS:
        if v0 <= va < v0 + sz:
            return nm
    return None


def read_va(va, n):
    for nm, v0, sz, data in SECS:
        if v0 <= va < v0 + sz:
            off = va - v0
            return data[off:off + n]
    return b""


def u32(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def read_cstr(va, maxn=200):
    out = bytearray()
    for i in range(maxn):
        b = read_va(va + i, 1)
        if not b or b[0] == 0:
            break
        out += b
    return out.decode("latin1", "replace")


def in_text(va):
    return TEXT_VA <= va < TEXT_END


_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True


def disasm(va, data):
    return list(_md.disasm(data, va)) if data else []


def disasm_body(va, size):
    return disasm(va, read_va(va, size or 512))


# ---------------- atlas ----------------
def load_atlas():
    a = {}
    with open(ATLAS_TSV, encoding="utf-8-sig") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if not row or not row[0].strip():
                continue
            try:
                a[row[0].strip().upper()] = {"size": int(row[1]), "n_instr": int(row[2])}
            except (ValueError, IndexError):
                pass
    return a


ATLAS = load_atlas()
_FUNCS = sorted((int(k, 16), k, v["size"]) for k, v in ATLAS.items())
_FSTARTS = [f[0] for f in _FUNCS]


def func_of(va):
    """覆盖 va 的最小 atlas 函数（返回 (start, key, size)）。"""
    i = bisect.bisect_right(_FSTARTS, va) - 1
    while i >= 0:
        s, k, sz = _FUNCS[i]
        if s <= va < s + sz:
            return (s, k, sz)
        if i > 0 and _FUNCS[i - 1][0] + _FUNCS[i - 1][2] <= va and s < va - 0x4000:
            break
        i -= 1
    return None


# ---------------- ② RTTI 通道 ----------------
def find_dword_refs(target, skip_text=False):
    """全镜像中 dword == target 的 VA 列表 [(va, section)]。"""
    needle = struct.pack("<I", target & 0xFFFFFFFF)
    out = []
    for nm, v0, size, data in SECS:
        if skip_text and nm == ".text":
            continue
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0:
                break
            out.append((v0 + i, nm))
            st = i + 1
    return out


def parse_col(col_va):
    if not col_va or sec_of(col_va) is None:
        return None
    return {"col": col_va, "sig": u32(col_va), "td": u32(col_va + 0xC),
            "chd": u32(col_va + 0x10)}


def parse_td(td_va):
    if not td_va or sec_of(td_va) is None:
        return None
    return {"td": td_va, "name_va": td_va + 8, "name": read_cstr(td_va + 8, 200)}


def resolve_slot(ref_va, maxk=64):
    """给槽 VA，回扫找 vt_base：要求 [vt-4]=COL(sig==0) 且 COL.TD+8 是 .?AV 名串。
    返回 dict(vtable_base, slot_off, slot_no, col, td, name_va, rtti)。"""
    for k in range(0, maxk + 1):
        vb = ref_va - 4 * k
        c = u32(vb - 4)
        if not c:
            continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return {"vtable_base": vb, "slot_off": 4 * k, "slot_no": k,
                    "col": ci["col"], "td": tdi["td"], "name_va": tdi["name_va"],
                    "rtti": tdi["name"]}
    return None


def enum_vtables():
    """枚举全镜像（非 .text）中所有「[p]=COL → vt_base=p+4 → 连续 .text 指针」的虚表。
    返回 [{vtable_base, col, td, name_va, rtti, slots:[...], n_slots}]。
    这样槽号是枚举出来的，不靠回扫猜测（避免 maxk 截断）。"""
    out = []
    for nm, v0, size, data in SECS:
        if nm == ".text":
            continue
        n = len(data) - 4
        for off in range(0, n + 1, 4):
            col = struct.unpack_from("<I", data, off)[0]
            if not (IB <= col < IB + 0x2000000):
                continue
            ci = parse_col(col)
            if not ci or ci["sig"] != 0:
                continue
            tdi = parse_td(ci["td"])
            if not tdi or ".?AV" not in (tdi["name"] or ""):
                continue
            vb = v0 + off + 4
            slots = []
            q = vb
            while True:
                v = u32(q)
                if v is None or not in_text(v):
                    break
                slots.append(v)
                q += 4
                if len(slots) > 400:
                    break
            if not slots:
                continue
            out.append({"vtable_base": vb, "vt_sec": nm, "col": ci["col"],
                        "td": tdi["td"], "name_va": tdi["name_va"], "rtti": tdi["name"],
                        "slots": slots, "n_slots": len(slots)})
    return out


VTABLES = None


def vtables():
    global VTABLES
    if VTABLES is None:
        VTABLES = enum_vtables()
    return VTABLES


def ring2(entry):
    """② 独立取证：枚举所有「slot 值 == entry」的虚表，逐表给 RTTI 类名与槽号。"""
    hits = []
    for vt in vtables():
        for i, v in enumerate(vt["slots"]):
            if v == entry:
                hits.append({"vtable_base": vt["vtable_base"], "slot_no": i,
                             "slot_off": 4 * i, "slot_va": vt["vtable_base"] + 4 * i,
                             "col": vt["col"], "td": vt["td"],
                             "rtti": vt["rtti"], "n_slots": vt["n_slots"],
                             "slot_value_ok": (u32(vt["vtable_base"] + 4 * i) == entry)})
                break
    return hits


def class_of(rtti_name):
    """'.?AVAnimClass@@' -> 'AnimClass'"""
    s = rtti_name or ""
    if s.startswith(".?AV"):
        s = s[4:]
    if s.endswith("@@"):
        s = s[:-2]
    return s


def match_vt_for_name(hits, name):
    """从 ② 命中里挑出 RTTI 类名与行名 'Class::slotN' 的 Class 一致的那一张。"""
    cls = name.split("::")[0] if "::" in name else ""
    out = [h for h in hits if class_of(h["rtti"]) == cls]
    return out if out else hits


# ---------------- ④ 活虚表安装点 ----------------
def imm_stores(vt):
    """找 .text 中立即数==vt 且形如 `mov dword [mem], imm32` 的站点。
    返回 [(insn_va, op_str, bytes_hex, dest_kind, dest_global)]。"""
    out = []
    T, B = TEXT_DATA, TEXT_VA
    needle = struct.pack("<I", vt & 0xFFFFFFFF)
    offs, st = [], 0
    while True:
        i = T.find(needle, st)
        if i < 0:
            break
        offs.append(i)
        st = i + 1
    for off in offs:
        start = None
        kind = None
        if off >= 6 and T[off - 6] == 0xC7 and T[off - 5] == 0x05:
            start, kind = off - 6, "global"        # C7 05 disp32 imm32
        elif off >= 2 and T[off - 2] == 0xC7:
            start, kind = off - 2, "regdisp"       # C7 modrm imm32
        if start is None:
            continue
        va = B + start
        insns = list(_md.disasm(read_va(va, 12), va))
        if not insns:
            continue
        ins = insns[0]
        if ins.address != va or ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        a, b = ins.operands
        if a.type != X86_OP_MEM or b.type != X86_OP_IMM:
            continue
        if (b.imm & 0xFFFFFFFF) != vt:
            continue
        dest_global = None
        if kind == "global":
            dest_global = struct.unpack("<I", T[off - 4:off])[0]
        out.append({"va": va, "op": ins.op_str, "bytes": ins.bytes.hex(),
                    "kind": kind, "dest_global": dest_global})
    return out


def atexit_sites(func_va, window=0x60):
    """`push <func_va>` 之后 window 内出现 `call 0x7C978A` ⇒ atexit 注册点（㉓ 死表侧）。"""
    needle = b"\x68" + struct.pack("<I", func_va & 0xFFFFFFFF)
    T, B = TEXT_DATA, TEXT_VA
    res, st = [], 0
    while True:
        i = T.find(needle, st)
        if i < 0:
            break
        for j in range(i + 5, min(i + 5 + window, len(T) - 5)):
            if T[j] == 0xE8:
                rel = struct.unpack_from("<i", T, j + 1)[0]
                if (B + j + 5 + rel) & 0xFFFFFFFF == ATEXIT_VA:
                    res.append((B + i, B + j))
                    break
        st = i + 1
    return res


def is_atexit(func_va):
    return bool(atexit_sites(func_va))


def ring4(entry, vt, slot_off, self_size):
    """④ 取证：枚举 vt 的全部立即数安装点，标注所在函数 / atexit / 是否行内。"""
    ea = entry
    out = []
    for s in imm_stores(vt):
        f = func_of(s["va"])
        fk = f[1] if f else None
        out.append({
            "va": s["va"], "op": s["op"], "bytes": s["bytes"], "kind": s["kind"],
            "dest_global": s["dest_global"],
            "in_func": fk, "in_func_va": f[0] if f else None,
            "atexit": bool(is_atexit(f[0])) if f else None,
            "in_self": (ea <= s["va"] < ea + self_size),
        })
    live = [x for x in out if x["atexit"] is False and not x["in_self"]]
    return {"stores": out, "n_live_outside": len(live), "live": live}


def direct_calls(target):
    out = []
    T, B = TEXT_DATA, TEXT_VA
    for off in range(0, len(T) - 5):
        if T[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", T, off + 1)[0]
        if (B + off + 5 + rel) & 0xFFFFFFFF == target:
            out.append(B + off)
    return out


# ---------------- ③b② 机械站点 ----------------
JCC = {"je", "jne", "jl", "jle", "jg", "jge", "ja", "jae", "jb", "jbe",
       "js", "jns", "jo", "jno", "jp", "jnp", "jz", "jnz"}


def _is_eax(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX


def test_kind(ins):
    if ins.id == X86_INS_TEST and len(ins.operands) == 2 and \
            _is_eax(ins.operands[0]) and _is_eax(ins.operands[1]):
        return ("test_eax", None)
    if ins.id == X86_INS_OR and len(ins.operands) == 2 and \
            _is_eax(ins.operands[0]) and _is_eax(ins.operands[1]):
        return ("or_eax", None)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2 and \
            _is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM:
        return ("cmp_imm", ins.operands[1].imm & 0xFFFFFFFF)
    return None


def path_sig(insns, start_idx, maxn=20):
    calls, rets = [], []
    end_eax = None
    eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.append(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 and \
                _is_eax(ins.operands[0]) and _is_eax(ins.operands[1]):
            eax = 0
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2:
            if _is_eax(ins.operands[0]):
                b = ins.operands[1]
                eax = (b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else None
        elif ins.id == X86_INS_RET:
            end_eax = eax
            if eax is not None:
                rets.append(eax)
            return {"calls": calls, "rets": rets, "end_eax": end_eax, "terminated": "ret"}
        elif ins.id == X86_INS_JMP:
            end_eax = eax
            return {"calls": calls, "rets": rets, "end_eax": end_eax, "terminated": "jmp"}
        else:
            end_eax = eax
    return {"calls": calls, "rets": rets, "end_eax": end_eax, "terminated": None}


def channel_a(insns, window_test=4, window_jcc=3):
    """③b② 机械站点：call → test/cmp eax → jcc，两条路径动作签名真不同。"""
    idx = {ins.address: i for i, ins in enumerate(insns)}
    sites = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        callee = None
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
        for k in range(i + 1, min(i + 1 + window_test, len(insns))):
            tk = test_kind(insns[k])
            if not tk:
                continue
            # eax 覆写陷阱：test 与 jcc 之间若有 mov eax,... 则不作数
            for m in range(k + 1, min(k + 1 + window_jcc, len(insns))):
                jc = insns[m]
                if jc.mnemonic not in JCC:
                    continue
                # 检查 k..m 之间 eax 是否被覆写
                eax_clobber = None
                for q in range(k + 1, m):
                    qi = insns[q]
                    if qi.id == X86_INS_MOV and qi.operands and _is_eax(qi.operands[0]):
                        eax_clobber = hx(qi.address)
                    if qi.id in (X86_INS_CALL,):
                        eax_clobber = hx(qi.address)
                tgt = jc.operands[0].imm if jc.operands and jc.operands[0].type == X86_OP_IMM else None
                ti = idx.get(tgt)
                sig_t = path_sig(insns, ti) if ti is not None else \
                    {"calls": [], "rets": [], "end_eax": None, "terminated": "OUT_OF_BODY"}
                sig_f = path_sig(insns, m + 1)
                sites.append({
                    "call_addr": ins.address, "callee": callee,
                    "test_addr": insns[k].address, "test_kind": tk[0], "test_imm": tk[1],
                    "jcc_addr": jc.address, "jcc": jc.mnemonic, "jcc_target": tgt,
                    "fallthrough": jc.address + jc.size,
                    "eax_clobber": eax_clobber,
                    "sig_taken": sig_t, "sig_fall": sig_f,
                    "same_action": (sig_t["calls"] == sig_f["calls"] and
                                    sig_t["rets"] == sig_f["rets"] and
                                    sig_t["end_eax"] == sig_f["end_eax"]),
                })
                break
            break
    return sites


def body_end_check(entry, size):
    """① 末条是否 ret/jmp；skipdata 造成 id==0 的条数。"""
    insns = disasm_body(entry, size)
    if not insns:
        return {"ok": False, "why": "no insn"}
    skip = sum(1 for i in insns if i.id == 0)
    last = insns[-1]
    covered = last.address + last.size - entry
    return {"ok": last.mnemonic in ("ret", "jmp", "retn"), "skipdata": skip,
            "last": "%s %s" % (last.mnemonic, last.op_str),
            "last_va": last.address, "covered": covered, "n_insn": len(insns)}


def callee_profile(callee_va, cap=None):
    """被调返回约定画像：每个 ret 前 eax 的来源（imm 常量 / call / 未知），
    以及该函数体内出现的可证伪常量。"""
    if not in_text(callee_va):
        return None
    key = hx(callee_va)
    cap = cap or (ATLAS.get(key, {}).get("size") or 0)
    if not cap:
        return None
    insns = disasm_body(callee_va, cap)
    consts, origins, rets = [], [], []
    eax = None
    for ins in insns:
        if ins.id == 0:
            continue
        if ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 and \
                _is_eax(ins.operands[0]) and _is_eax(ins.operands[1]):
            eax = ("imm", 0)
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2 and _is_eax(ins.operands[0]):
            b = ins.operands[1]
            if b.type == X86_OP_IMM:
                eax = ("imm", b.imm & 0xFFFFFFFF)
            elif b.type == X86_OP_MEM:
                eax = ("mem", ins.op_str)
            else:
                eax = ("reg", ins.op_str)
        elif ins.id == X86_INS_CALL:
            eax = ("call", hx(ins.operands[0].imm) if ins.operands and
                   ins.operands[0].type == X86_OP_IMM else "ind")
        elif ins.id in (X86_INS_OR,) and len(ins.operands) == 2 and _is_eax(ins.operands[0]) \
                and ins.operands[1].type == X86_OP_IMM:
            eax = ("imm", (eax[1] | ins.operands[1].imm) & 0xFFFFFFFF
                   if eax and eax[0] == "imm" else None)
        elif ins.id == X86_INS_RET:
            rets.append({"va": ins.address, "eax": eax,
                         "ret_imm": ins.operands[0].imm if ins.operands and
                         ins.operands[0].type == X86_OP_IMM else 0})
            if eax and eax[0] == "imm" and eax[1] is not None:
                consts.append(eax[1])
            eax = None
    return {"callee": hx(callee_va), "n_rets": len(rets), "rets": rets,
            "consts": sorted(set(consts)), "n_insn": len(insns),
            "insns": insns}


def is_falsifiable(v):
    if v in (0, 1, 0xFFFFFFFF):
        return True
    if 0x80000000 <= v <= 0x8FFFFFFF:
        return True
    if 0xC0000000 <= v <= 0xDFFFFFFF:
        return True
    return False


def dump(va, size, title=""):
    """反汇编 dump 成文本行（供 EVIDENCE 引用）。"""
    out = []
    if title:
        out.append(title)
    for ins in disasm_body(va, size):
        b = ins.bytes.hex()
        out.append("%08X  %-20s %-8s %s" % (ins.address, b, ins.mnemonic, ins.op_str))
    return "\n".join(out)


if __name__ == "__main__":
    print("text=[%08X,%08X) atlas=%d" % (TEXT_VA, TEXT_END, len(ATLAS)))
    print("self-check S14 00691EE0 ring2:", ring2(0x00691EE0)["n_rtti_slots"], "rtti slots")
