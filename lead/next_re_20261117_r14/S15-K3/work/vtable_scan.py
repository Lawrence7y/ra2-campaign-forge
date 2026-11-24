#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1) look up event L1 handlers in coverage  2) scan .rdata for candidate-as-vtable-slot with RTTI COL/TD name"""
import sys, csv, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
cov={}
with open(COV,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        cov[(r['entry'] or '').strip().lower()]=(r['name'],r['grade'],r['subsystem'],r['one_line_semantics'])
atlas=set()
with open(ATL,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        atlas.add((r['entry'] or '').strip().lower())

print("=== event L1 handlers in coverage / atlas? ===")
for i in range(12):
    h=p.dword_va(0x71F218+4*i)
    key=f"{h:08x}"
    c=cov.get(key)
    print(f"L1[{i:2d}]=0x{h:08X} in_atlas={key in atlas} coverage={c}")

CAND = [
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
]
cset=set(CAND)

# scan .rdata dword-aligned for candidate values; group by "slot" position before COL
RVA0=0x7e1000
RSZ=0x30074
rdata = p._pe.get_data(RVA0, RSZ)  # bytes
base_va = 0x400000+RVA0
hits={c:[] for c in CAND}
for off in range(0, len(rdata)-8, 4):
    val=int.from_bytes(rdata[off:off+4],'little')
    if val in cset:
        va=base_va+off
        # check preceding dword = COL? try RTTI: at va-4 maybe COL pointer (vtable[-1])
        prev=int.from_bytes(rdata[off-4:off],'little') if off>=4 else 0
        hits[val].append((va,prev))

def rtti_name(col):
    """given COL va (points to COL struct: pFirstBase/vfptr/...; TD at COL+0xC)"""
    if not (0x400000<=col<0x900000): return None
    try:
        td=p.dword_va(col+0xC)
        if not (0x400000<=td<0x900000): return None
        # TD: +8 name (inline null-terminated string)
        namep=p.dword_va(td+8)
        if not (0x400000<=namep<0x900000): return None
        b=p.read_va(namep,64)
        s=b.split(b'\x00')[0]
        s=s.decode('ascii',errors='replace')
        return (td,s)
    except Exception:
        return None

print()
print("=== candidate occurrences in .rdata (possible vtable slots) ===")
for c in CAND:
    hs=hits[c]
    print(f"0x{c:08X}: {len(hs)} hits")
    for va,prev in hs[:12]:
        r1=rtti_name(prev)
        # also try: this va is vtable[k], and COL is at vtable[0]-... no; try prev as COL directly
        info=f" prev=0x{prev:08X}"
        if r1: info+=f" -> TD=0x{r1[0]:08X} name='{r1[1]}'"
        print(f"    slot@0x{va:08X}{info}")
