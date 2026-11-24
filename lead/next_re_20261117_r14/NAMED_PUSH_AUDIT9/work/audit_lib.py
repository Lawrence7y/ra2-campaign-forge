# -*- coding: utf-8 -*-
"""NAMED_PUSH_AUDIT9 异族独立审计库。
只读 gamemd.exe，自己解析 PE + capstone(skipdata=True) 反汇编。
不 import、不复用 NAMED_PUSH_S12_B2\\_work 下任何执行器代码；
不读取 EVIDENCE/ROW_*.txt 作为证据。
"""
import os, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
_pe = pefile.PE(EXE)
IB = _pe.OPTIONAL_HEADER.ImageBase

SECS = []  # (name, va, vsize, rawdata)
for s in _pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    vs = max(s.Misc_VirtualSize, s.SizeOfRawData)
    SECS.append((nm, va, vs, s.get_data()[: s.SizeOfRawData]))

TEXT_VA = None
for nm, v0, vs, d in SECS:
    if nm == ".text":
        TEXT_VA, TEXT_VSIZE, TEXT_DATA = v0, vs, d
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

def hx(x): return "%08X" % (x & 0xFFFFFFFF)

def in_text(va): return TEXT_LO <= (va & 0xFFFFFFFF) < TEXT_HI

def va_sec(va):
    va &= 0xFFFFFFFF
    for nm, v0, vs, data in SECS:
        if v0 <= va < v0 + vs:
            return nm
    return None

def va_read(va, n):
    va &= 0xFFFFFFFF
    for nm, v0, vs, data in SECS:
        if v0 <= va < v0 + vs:
            off = va - v0
            return data[off: off + n] if off + n <= len(data) else data[off:]
    return b""

def u32(va):
    b = va_read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None

def i32(va):
    b = va_read(va, 4)
    return struct.unpack("<i", b)[0] if len(b) == 4 else None

def u8(va):
    b = va_read(va, 1)
    return b[0] if b else None

def read_cstr(va, maxn=300):
    out = bytearray()
    for i in range(maxn):
        b = va_read(va + i, 1)
        if not b or b[0] == 0:
            break
        out += b
    return out.decode("latin1", "replace")

def hexb(va, n):
    return " ".join("%02X" % c for c in va_read(va, n))

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def disasm(va, n):
    data = va_read(va, n)
    return list(_md.disasm(data, va)) if data else []

def fmt_ins(ins):
    return "%08X  %-20s %-8s %s" % (ins.address, hexb(ins.address, ins.size), ins.mnemonic, ins.op_str)

# ---- RTTI ----
def parse_col(cva):
    if not cva or va_sec(cva) is None: return None
    return dict(col=cva, sig=u32(cva), td=u32(cva + 0xC))

def parse_td(tva):
    if not tva or va_sec(tva) is None: return None
    return dict(td=tva, name=read_cstr(tva + 8, 300))

def resolve_slot(refva, maxk=400):
    """槽 VA -> vtable base（回扫 [-4]==COL, COL.sig==0, TD 名 .?AV），返回第一命中。"""
    for k in range(0, maxk + 1):
        vb = (refva - 4 * k) & 0xFFFFFFFF
        c = u32(vb - 4)
        if not c: continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0: continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"].startswith(".?AV"):
            return dict(vtable_base=vb, slot_off=4 * k, slot_index=k,
                        col=ci["col"], td=tdi["td"], rtti_name=tdi["name"])
    return None

def find_dword_refs(target, skip_text=True):
    needle = struct.pack("<I", target & 0xFFFFFFFF)
    refs = []
    for nm, v0, vs, data in SECS:
        if skip_text and nm == ".text": continue
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0: break
            refs.append((v0 + i, nm))
            st = i + 1
    return refs

# ---- .text 安装点 / atexit / direct call ----
def find_vtable_imm_sites(vtable_addr):
    needle = struct.pack("<I", vtable_addr & 0xFFFFFFFF)
    out = []
    st = 0
    while True:
        i = TEXT_DATA.find(needle, st)
        if i < 0: break
        va = TEXT_VA + i
        form = "?"
        write_va = None
        if i >= 6 and TEXT_DATA[i-6] == 0xC7 and TEXT_DATA[i-5] == 0x05:
            form = "C7 05 (mov [global],imm)"; write_va = va - 6
        elif i >= 2 and TEXT_DATA[i-2] == 0xC7:
            form = "C7 /0 (mov [mem],imm)"; write_va = va - 2
        if i >= 1 and 0xB8 <= TEXT_DATA[i-1] <= 0xBF:
            form += " | B8+r (mov reg,imm)"
        out.append(dict(imm_va=va, form=form, write_va=write_va))
        st = i + 1
    return out

ATEXIT_CALL = 0x7C978A
def is_atexit_registered(func_va):
    needle = b"\x68" + struct.pack("<I", func_va & 0xFFFFFFFF)
    hits = []
    st = 0
    while True:
        i = TEXT_DATA.find(needle, st)
        if i < 0: break
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
        if TEXT_DATA[off] != 0xE8: continue
        rel = struct.unpack_from("<i", TEXT_DATA, off + 1)[0]
        if (TEXT_VA + off + 5 + rel) & 0xFFFFFFFF == t:
            out.append(TEXT_VA + off)
    return out

# ---- 被调返回常量集合：线性扫函数体所有 ret 前最近 mov/xor eax ----
def eax_constants(va, n):
    """返回 [(ret_va, const_or_None)]，按反汇编顺序。"""
    insns = disasm(va, n)
    res = []
    last = None
    for ins in insns:
        if ins.id == 0:  # skipdata
            continue
        if ins.id == X86_INS_MOV and len(ins.operands) == 2:
            o0, o1 = ins.operands
            if o0.type == X86_OP_REG and o0.reg == X86_REG_EAX:
                if o1.type == X86_OP_IMM:
                    last = o1.imm & 0xFFFFFFFF
                elif o1.type == X86_OP_REG and o1.reg == X86_REG_EAX:
                    pass
                else:
                    last = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2:
            o0, o1 = ins.operands
            if o0.type == X86_OP_REG and o0.reg == X86_REG_EAX and \
               o1.type == X86_OP_REG and o1.reg == X86_REG_EAX:
                last = 0
        elif ins.id == X86_INS_CALL:
            last = None
        elif ins.id == X86_INS_RET:
            res.append((ins.address, last, ins.mnemonic, ins.op_str))
            last = None
    return res

if __name__ == "__main__":
    print("IB=%08X text=[%08X,%08X) .text_va=%08X" % (IB, TEXT_LO, TEXT_HI, TEXT_VA))
    for nm, v0, vs, d in SECS:
        print("  %-8s %08X +%X" % (nm, v0, vs))
