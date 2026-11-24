#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态列出若干候选 vt -> RTTI 类名（COL+0xC->TD+8）。"""
import pefile
GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(GAME, fast_load=True)
DATA = open(GAME, "rb").read()
IB = pe.OPTIONAL_HEADER.ImageBase

def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            off = s.PointerToRawData + (rva - s.VirtualAddress)
            if off < len(DATA):
                return off
    return None
def u32(va):
    o = va2off(va)
    return int.from_bytes(DATA[o:o+4], "little") if o is not None and o+4<=len(DATA) else None
def name(va):
    vptr = va
    col = u32(vptr-4)
    if not col: return None
    td = u32(col+0xC)
    if not td: return None
    raw=b""
    for i in range(96):
        o=va2off(td+8+i)
        if o is None: break
        b=DATA[o]
        if b==0: break
        raw+=bytes([b])
    return raw.decode('latin-1','replace') if raw.startswith(b'.?A') else raw.decode('latin-1','replace')

VTS=[0x7e3ebc,0x7f5c70,0x7eb058,0x7e3e00,0x7eb000,0x7eb100]
for vt in VTS:
    print(hex(vt),'->',name(vt))
