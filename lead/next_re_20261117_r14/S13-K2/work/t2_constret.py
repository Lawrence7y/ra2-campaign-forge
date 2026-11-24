#!/usr/bin/env python3
"""List S13 entries whose function body starts with B8 imm32 C3 (constant-return).
Also read 0x7E2224 as float/dword per 'fmul dword'."""
import sys, os, csv, struct
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R
ROOT=r"D:\Project\ra2-campaign-forge"
TGT=os.path.join(ROOT,r"lead\next_re_20261117_r14\S13-K2\TARGETS.tsv")
print("0x7E2224 dword=0x%08X float=%r ; 0x7E2800 dword=0x%08X" % (
    R.u32(0x7E2224), struct.unpack('<f',R.read(0x7E2224,4))[0], R.u32(0x7E2800)))

print("\n=== S13 entries: function body B8 imm32 C3 (constant return) ===")
rows=list(csv.DictReader(open(TGT,encoding="utf-8",errors="replace"),delimiter="\t"))
n=0
for r in rows:
    a=int(r["entry"],16)
    b=R.read(a,6)
    if len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
        imm=struct.unpack('<I',b[1:5])[0]
        print(f"  {r['entry']} {r['name']:<32} grade={r['grade']:<10} imm=0x{imm:X}({imm})  sem={r['semantics'][:30]}")
        n+=1
print("  total:",n)

print("\n=== S13 entries named GetSize/WhatAmI/Maximum ===")
for r in rows:
    nm=r["name"].lower()
    if any(k in nm for k in ("getsize","whatami","maximum","size")):
        a=int(r["entry"],16); b=R.read(a,6)
        print(f"  {r['entry']} {r['name']:<32} grade={r['grade']:<10} bytes={b.hex()}")
