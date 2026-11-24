#!/usr/bin/env python3
"""re_lib for S13-K2. capstone skipdata=True; pefile. VA-based (ImageBase 0x400000)."""
import pefile
from capstone import *
from capstone.x86 import *

PE_PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

pe = pefile.PE(PE_PATH, fast_load=True)
DATA = open(PE_PATH, "rb").read()
SECS = []
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\x00").decode("latin1"),
                 s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def va_to_off(va):
    rva = va - IB
    for name, va0, vsz, raw, rsz in SECS:
        if va0 <= rva < va0 + max(vsz, rsz):
            off = raw + (rva - va0)
            if off < len(DATA):
                return off
    return None

def read(va, n):
    o = va_to_off(va)
    if o is None:
        return b""
    return DATA[o:o+n]

def u8(va):
    b = read(va, 1); return b[0] if b else None
def u16(va):
    b = read(va, 2); return int.from_bytes(b, "little") if len(b) >= 2 else None
def u32(va):
    b = read(va, 4); return int.from_bytes(b, "little") if len(b) >= 4 else None
def u64(va):
    b = read(va, 8); return int.from_bytes(b, "little") if len(b) >= 8 else None

def disasm(va, max_bytes=256, count=0):
    code = read(va, max_bytes)
    out = []
    for i in md.disasm(code, va):
        out.append(i)
        if count and len(out) >= count:
            break
    return out

def fmt(ins):
    return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}"

def dump(va, max_bytes=256, count=0):
    return "\n".join(fmt(i) for i in disasm(va, max_bytes, count))

def section_of(va):
    rva = va - IB
    for name, va0, vsz, raw, rsz in SECS:
        if va0 <= rva < va0 + max(vsz, rsz):
            return name
    return "?"

def find_bytes(pattern, start_va=None, end_va=None, limit=200):
    res = []
    o0 = 0 if start_va is None else (va_to_off(start_va) or 0)
    o1 = len(DATA) if end_va is None else (va_to_off(end_va) or len(DATA))
    idx = DATA.find(pattern, o0, o1)
    while idx != -1 and len(res) < limit:
        for name, va0, vsz, raw, rsz in SECS:
            if raw <= idx < raw + rsz:
                res.append(IB + va0 + (idx - raw))
                break
        idx = DATA.find(pattern, idx + 1, o1)
    return res

def insn_has_disp(ins, disp):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.disp == disp:
            return True
    return False

if __name__ == "__main__":
    print("SECTIONS (name, RVA, VSize, RawPtr, RawSize):")
    for s in SECS:
        print("  %-10s RVA=0x%08X VSize=0x%X Raw=0x%08X RawSize=0x%X VA=0x%08X" %
              (s[0], s[1], s[2], s[3], s[4], IB+s[1]))
    print("data len:", len(DATA))
