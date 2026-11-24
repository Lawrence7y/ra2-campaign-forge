# -*- coding: utf-8 -*-
"""Shared helpers for D41-SUBST. Read-only on gamemd.exe."""
import struct, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
IB = 0x400000

_pe = pefile.PE(EXE, fast_load=True)
SECS = []
for s in _pe.sections:
    name = s.Name.rstrip(b"\0").decode("latin1")
    SECS.append((name, s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
DATA = open(EXE, "rb").read()

def sec_of_rva(rva):
    for name, va, vs, rs, ra in SECS:
        if va <= rva < va + max(vs, rs):
            return name, va, vs, rs, ra
    return None

def rva2off(rva):
    s = sec_of_rva(rva)
    if s is None:
        return None
    name, va, vs, rs, ra = s
    d = rva - va
    return ra + d if d < rs else None

def va2off(va):
    return rva2off(va - IB)

def read_va(va, n):
    o = va2off(va)
    if o is None or o < 0 or o + n > len(DATA):
        return None
    return DATA[o:o+n]

def u32(va):
    b = read_va(va, 4)
    return None if b is None else struct.unpack("<I", b)[0]

def find_dword(val, limit=1000):
    pat = struct.pack("<I", val & 0xffffffff)
    hits = []
    i = DATA.find(pat)
    while i >= 0 and len(hits) < limit:
        hits.append(i)
        i = DATA.find(pat, i + 1)
    return hits

def off2va(off):
    for name, va, vs, rs, ra in SECS:
        if ra <= off < ra + rs:
            return IB + va + (off - ra)
    return None

def where_va(va):
    s = sec_of_rva(va - IB)
    return s[0] if s else "?"

def md32():
    m = Cs(CS_ARCH_X86, CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m

def disasm_va(va, size):
    o = va2off(va)
    if o is None:
        return []
    return list(md32().disasm(DATA[o:o+size], va))

if __name__ == "__main__":
    print("SHA check:", __import__("hashlib").sha256(DATA).hexdigest() == SHA)
    print("sections:")
    for s in SECS:
        print("  %-8s VA=%08X VS=%d RS=%d RA=%08X" % s)
