# -*- coding: utf-8 -*-
"""NAMED-PUSH S12 B1 反汇编/取证核心（本目录自建，不复用其它卡 work 代码）。

提供：
 - PE 段表 + VA 读写（按 VirtualSize）
 - atlas 函数边界
 - capstone 5.0.7 skipdata=True 反汇编
 - RTTI 链解析：vtable base -> [-4]=COL -> [COL+0xC]=TD -> TD+8 = .?AV...@@
 - 全镜像 dword 引用扫描（vtable 槽候选）
 - .text 中 vtable 立即数安装点（C7 05 disp32 imm32 / C7 modrm imm32 / B8+r imm32）
 - atexit 判定（push <fn>; call 0x7C978A）
 - direct caller 扫描
 - ③b② 机械站点筛选（call -> test/cmp eax -> jcc，eax 不覆写，两路动作签名不同）
 - ③b① 跳转表解析
所有地址输出 "%08X" 大写无 0x。
"""
import csv, os, struct, pefile
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")


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


_pe = pefile.PE(EXE)
IB = _pe.OPTIONAL_HEADER.ImageBase

SECS = []          # (name, va, vsize, rawdata)
for _s in _pe.sections:
    _nm = _s.Name.rstrip(b"\x00").decode("latin1")
    _va = IB + _s.VirtualAddress
    _vs = max(_s.Misc_VirtualSize, _s.SizeOfRawData)
    SECS.append((_nm, _va, _vs, _s.get_data()[: _s.SizeOfRawData]))


def _sec_by_name(nm):
    for s in SECS:
        if s[0] == nm:
            return s
    return None


_t = _sec_by_name(".text")
TEXT_VA, TEXT_VSIZE, TEXT_DATA = _t[1], _t[2], _t[3]
# 卡片：.text = [0x401000, 0x7E038D)
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D


def in_text(va):
    return TEXT_LO <= va < TEXT_HI


def va_sec(va):
    for nm, v0, vs, data in SECS:
        if v0 <= va < v0 + vs:
            return nm
    return None


def va_read(va, n):
    for nm, v0, vs, data in SECS:
        if v0 <= va < v0 + vs:
            off = va - v0
            if off + n <= len(data):
                return data[off: off + n]
            return data[off:]
    return b""


def u32(va):
    b = va_read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def i32(va):
    b = va_read(va, 4)
    return struct.unpack("<i", b)[0] if len(b) == 4 else None


def read_cstr(va, maxn=260):
    out = bytearray()
    for i in range(maxn):
        b = va_read(va + i, 1)
        if not b or b[0] == 0:
            break
        out += b
    return out.decode("latin1", "replace")


def load_atlas():
    a = {}
    with open(ATLAS, encoding="utf-8-sig") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if not row or not row[0].strip():
                continue
            try:
                a[norm(row[0])] = dict(size=int(row[1]), n_instr=int(row[2]))
            except (ValueError, IndexError):
                pass
    return a


ATLAS = load_atlas()


def atlas_covering(va):
    """覆盖 va 的最小（最内层）atlas 函数 entry。"""
    best = None
    for e, info in ATLAS.items():
        ea = int(e, 16)
        if ea <= va < ea + info["size"]:
            if best is None or ea > best[0]:
                best = (ea, e, info["size"])
    return best


_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True


def disasm(va, n):
    data = va_read(va, n)
    return list(_md.disasm(data, va)) if data else []


def disasm_body(entry_hex):
    e = int(norm(entry_hex), 16)
    cap = ATLAS.get(norm(entry_hex), {}).get("size") or 512
    return e, disasm(e, cap)


# ---------------- RTTI ----------------
def parse_col(col_va):
    if not col_va or va_sec(col_va) is None:
        return None
    sig = u32(col_va)
    td = u32(col_va + 0xC)
    chd = u32(col_va + 0x10)
    return dict(col=col_va, sig=sig, td=td, chd=chd)


def parse_td(td_va):
    if not td_va or va_sec(td_va) is None:
        return None
    return dict(td=td_va, name_va=td_va + 8, name=read_cstr(td_va + 8, 260))


def resolve_slot(refva, maxk=60):
    """槽 VA -> vtable base（回扫找 [-4]==COL, COL.sig==0, TD 名 .?AV）。返回第一命中。"""
    out = []
    for k in range(0, maxk + 1):
        vb = refva - 4 * k
        c = u32(vb - 4)
        if not c:
            continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"].startswith(".?AV"):
            out.append(dict(vtable_base=vb, slot_off=4 * k, slot_index=k,
                            col=ci["col"], td=tdi["td"], name_va=tdi["name_va"],
                            rtti_name=tdi["name"]))
            break
    return out[0] if out else None


def find_dword_refs(target, skip_text=True):
    needle = struct.pack("<I", target & 0xFFFFFFFF)
    refs = []
    for nm, v0, vs, data in SECS:
        if skip_text and nm == ".text":
            continue
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0:
                break
            refs.append((v0 + i, nm))
            st = i + 1
    return refs


# ---------------- .text 安装点 ----------------
def find_vtable_imm_sites(vtable_addr):
    """.text 中以立即数出现 vtable_addr 的点，并辨认指令形态。"""
    out = dict(c7_05=[], c7_rm=[], reg_load=[])
    needle = struct.pack("<I", vtable_addr & 0xFFFFFFFF)
    st = 0
    while True:
        i = TEXT_DATA.find(needle, st)
        if i < 0:
            break
        va = TEXT_VA + i
        if i >= 6 and TEXT_DATA[i - 6] == 0xC7 and TEXT_DATA[i - 5] == 0x05:
            out["c7_05"].append(dict(write_va=va - 6,
                                     global_=struct.unpack_from("<I", TEXT_DATA, i - 4)[0]))
        elif i >= 2 and TEXT_DATA[i - 2] == 0xC7:
            out["c7_rm"].append(dict(write_va=va - 2))
        if i >= 1 and 0xB8 <= TEXT_DATA[i - 1] <= 0xBF:
            out["reg_load"].append(dict(load_va=va - 1))
        st = i + 1
    return out


ATEXIT_CALL = 0x7C978A


def is_atexit_registered(func_va):
    """㉓：func_va 是否被 push 后紧接 call 0x7C978A（atexit 注册 = 析构器表）。"""
    needle = b"\x68" + struct.pack("<I", func_va & 0xFFFFFFFF)
    hits = []
    st = 0
    while True:
        i = TEXT_DATA.find(needle, st)
        if i < 0:
            break
        pushva = TEXT_VA + i
        for j in range(i + 5, min(i + 5 + 0x60, len(TEXT_DATA) - 5)):
            if TEXT_DATA[j] == 0xE8:
                rel = struct.unpack_from("<i", TEXT_DATA, j + 1)[0]
                if (TEXT_VA + j + 5 + rel) & 0xFFFFFFFF == ATEXIT_CALL:
                    hits.append((hx(pushva), hx(TEXT_VA + j)))
                    break
        st = i + 1
    return hits


def find_direct_calls(target):
    out = []
    t = target & 0xFFFFFFFF
    for off in range(0, len(TEXT_DATA) - 5):
        if TEXT_DATA[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", TEXT_DATA, off + 1)[0]
        if (TEXT_VA + off + 5 + rel) & 0xFFFFFFFF == t:
            out.append(TEXT_VA + off)
    return out


# ---------------- ③b② ----------------
JCC = set()
for _n in dir():
    if _n.startswith("X86_INS_J") and _n != "X86_INS_JMP":
        JCC.add(globals()[_n])


def _is_eax(o):
    return o.type == X86_OP_REG and o.reg == X86_REG_EAX


def test_kind(ins):
    if ins.id in (X86_INS_TEST, X86_INS_OR) and len(ins.operands) == 2 \
       and _is_eax(ins.operands[0]) and _is_eax(ins.operands[1]):
        return ("TEST_EAX" if ins.id == X86_INS_TEST else "OR_EAX", 0)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2 and _is_eax(ins.operands[0]) \
       and ins.operands[1].type == X86_OP_IMM:
        return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None


def writes_eax(ins):
    """该指令是否覆写 eax（保守：目的操作数含 eax 的 MOV/XOR/POP/算术等）。"""
    if ins.id == X86_INS_CALL:
        return True
    for o in ins.operands:
        if o.type == X86_OP_REG and o.reg == X86_REG_EAX and o.access & CS_AC_WRITE:
            return True
    if ins.regs_access():
        _, wr = ins.regs_access()
        if X86_REG_EAX in wr:
            return True
    return False


def path_sig(insns, start, maxn=20):
    calls, rets = set(), set()
    end_eax = None
    has_ret = False
    eax = None
    for j in range(start, min(start + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 \
                and _is_eax(ins.operands[0]) and _is_eax(ins.operands[1]):
            eax = 0
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2 and _is_eax(ins.operands[0]):
            b = ins.operands[1]
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
    return dict(calls=sorted(calls), rets=sorted(rets), has_ret=has_ret, end_eax=end_eax)


def sites_3b2(insns):
    """③b② 候选站点：call -> (<=3 条内) test/cmp eax -> (<=2 条内) jcc，
    test 与 jcc 之间 eax 不得被覆写；两路动作签名必须不同。"""
    idx = {i.address: k for k, i in enumerate(insns)}
    out = []
    for k, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        callee = ins.operands[0].imm & 0xFFFFFFFF if (ins.operands and ins.operands[0].type == X86_OP_IMM) else None
        for a in range(k + 1, min(k + 4, len(insns))):
            tk = test_kind(insns[a])
            if not tk:
                if writes_eax(insns[a]) and insns[a].id != X86_INS_CALL:
                    break
                continue
            gap_ok = True
            for b in range(a + 1, min(a + 3, len(insns))):
                jc = insns[b]
                if jc.id in JCC:
                    tgt = jc.operands[0].imm & 0xFFFFFFFF if (jc.operands and jc.operands[0].type == X86_OP_IMM) else None
                    ti = idx.get(tgt)
                    st = path_sig(insns, ti) if ti is not None else dict(calls=[], rets=[], has_ret=False, end_eax="OOB")
                    sf = path_sig(insns, b + 1)
                    same = (st["calls"] == sf["calls"] and st["rets"] == sf["rets"]
                            and st["has_ret"] == sf["has_ret"] and st["end_eax"] == sf["end_eax"])
                    out.append(dict(call_va=ins.address, callee=callee,
                                    test_va=insns[a].address, test_kind=tk[0], test_imm=tk[1],
                                    jcc_va=jc.address, jcc_mn=jc.mnemonic, jcc_target=tgt,
                                    fallthrough=jc.address + jc.size,
                                    sig_taken=st, sig_ft=sf, differ=not same,
                                    eax_overwritten_between=False))
                    break
                if writes_eax(jc):
                    gap_ok = False
                    break
            break
    return out


def jumptables(insns):
    out = []
    for k, ins in enumerate(insns):
        if ins.id != X86_INS_JMP or not ins.operands or ins.operands[0].type != X86_OP_MEM:
            continue
        op = ins.operands[0].mem
        if op.scale != 4 or op.index == X86_REG_INVALID:
            continue
        bound = None
        for j in range(k - 1, max(-1, k - 14), -1):
            p = insns[j]
            if p.id == X86_INS_CMP and len(p.operands) == 2 and p.operands[1].type == X86_OP_IMM:
                bound = p.operands[1].imm & 0xFFFFFFFF
                break
        table_va = None
        if op.base == X86_REG_INVALID and op.disp:
            table_va = op.disp & 0xFFFFFFFF
        if table_va is None:
            for j in range(k - 1, max(-1, k - 14), -1):
                p = insns[j]
                if p.id == X86_INS_MOV and len(p.operands) == 2 and p.operands[0].type == X86_OP_REG \
                   and p.operands[0].reg == op.base and p.operands[1].type == X86_OP_IMM:
                    table_va = (p.operands[1].imm & 0xFFFFFFFF) + (op.disp or 0)
                    break
        n = (bound + 1) if bound is not None else None
        tg = []
        if table_va and n and 1 <= n <= 300:
            for c in range(n):
                t = u32(table_va + c * 4)
                if t and in_text(t):
                    tg.append((c, t))
        out.append(dict(jmp_va=ins.address, op_str=ins.op_str, table_va=table_va,
                        bound=bound, ncase=n, targets=tg))
    return out


if __name__ == "__main__":
    print("text=[%08X,%08X) vsize=%d rdata 段表:" % (TEXT_LO, TEXT_HI, TEXT_VSIZE))
    for nm, v0, vs, d in SECS:
        print("  %-8s %08X +%X" % (nm, v0, vs))
    print("atlas=%d" % len(ATLAS))
