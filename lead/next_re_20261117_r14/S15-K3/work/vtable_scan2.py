#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan .rdata for candidate-as-vtable-slot with RTTI COL/TD class name"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p

CAND = [
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
]
cset=set(CAND)

# .rdata section raw bytes via file data
sec=None
for s in p._pe.sections:
    if s.Name.decode(errors='replace').rstrip('\x00')=='.rdata':
        sec=s; break
raw_off = sec.PointerToRawData
raw_sz  = sec.SizeOfRawData
data = p._pe.__data__[raw_off:raw_off+raw_sz]
base_va = 0x400000 + sec.VirtualAddress

def rtti_name(col):
    if not (0x400000<=col<0x900000): return None
    try:
        td=p.dword_va(col+0xC)
        if not (0x400000<=td<0x900000): return None
        namep=p.dword_va(td+8)
        if not (0x400000<=namep<0x900000): return None
        b=p.read_va(namep,80)
        s=b.split(b'\x00')[0].decode('ascii',errors='replace')
        return (td,s)
    except Exception:
        return None

hits={c:[] for c in CAND}
for off in range(0, len(data)-8, 4):
    val=int.from_bytes(data[off:off+4],'little')
    if val in cset:
        va=base_va+off
        prev=int.from_bytes(data[off-4:off],'little') if off>=4 else 0
        hits[val].append((va,prev))

for c in CAND:
    hs=hits[c]
    print(f"0x{c:08X}: {len(hs)} .rdata hits")
    for va,prev in hs[:16]:
        info=f" prev_dword=0x{prev:08X}"
        r1=rtti_name(prev)
        if r1: info+=f" -> TD=0x{r1[0]:08X} class='{r1[1]}' (prev IS COL)"
        # try prev as COL-0xC (i.e. search TD at prev)
        r2=rtti_name(prev-0xC)
        if r2 and not r1: info+=f" -> TD=0x{r2[0]:08X} class='{r2[1]}' (prev-0xC is COL)"
        print(f"    slot@0x{va:08X}{info}")
