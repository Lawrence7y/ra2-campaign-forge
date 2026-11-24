#!/usr/bin/env python3
"""S03-C8 self-contained binary helpers. No import from any other card.
Target gamemd.exe READ-ONLY. capstone skipdata=True."""
import os, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA, CS_OPT_SKIPDATA_SETUP

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
DATA = open(EXE, "rb").read()
SHA = hashlib.sha256(DATA).hexdigest()
assert SHA.upper().startswith("73201CC0") and SHA.upper().endswith("F67476"), SHA

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
# sections
SECS = []
for s in pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin-1')
    va = IB + s.VirtualAddress
    SECS.append((name, va, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

def sec(name):
    for n, va, vs, ro, rs in SECS:
        if n == name:
            return va, vs, ro, rs
    raise KeyError(name)

TEXT_VA, TEXT_VS, TEXT_RO, TEXT_RS = sec('.text')
RDATA_VA, RDATA_VS, RDATA_RO, RDATA_RS = sec('.rdata')

def va2off(va):
    for n, sva, vs, ro, rs in SECS:
        if sva <= va < sva + max(vs, rs):
            d = va - sva
            if d < rs:
                return ro + d
    raise ValueError("unmapped VA 0x%X" % va)

def ru32(va):
    try:
        o = va2off(va)
    except ValueError:
        return None
    if o + 4 > len(DATA):
        return None
    return struct.unpack_from('<I', DATA, o)[0]

def in_text(va):
    return TEXT_VA <= va < TEXT_VA + TEXT_VS

def md(va, size):
    cs = Cs(CS_ARCH_X86, CS_MODE_32)
    cs.skipdata = True
    return list(cs.disasm(DATA[va2off(va):va2off(va)+size], va))

def md_detail(va, size):
    cs = Cs(CS_ARCH_X86, CS_MODE_32)
    cs.skipdata = True
    cs.detail = True
    return list(cs.disasm(DATA[va2off(va):va2off(va)+size], va))

def insn_len_from(va, maxb=16):
    cs = Cs(CS_ARCH_X86, CS_MODE_32)
    cs.skipdata = True
    for i in cs.disasm(DATA[va2off(va):va2off(va)+maxb], va):
        return i.size
    return 1
