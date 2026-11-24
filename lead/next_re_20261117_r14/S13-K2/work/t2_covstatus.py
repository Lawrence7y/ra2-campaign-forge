#!/usr/bin/env python3
"""Check status of key T2 addresses in coverage/atlas; locate Verses loader entry."""
import sys, os, csv, struct
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
def norm(e): return e.strip().upper().replace("0X","").zfill(8)
cov={}
for r in csv.DictReader(open(COV,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("entry"): cov[norm(r["entry"])]=r
atl={}
for r in csv.DictReader(open(ATLAS,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("entry"): atl[norm(r["entry"])]=r

KEY={
 0x489180:"GetTotalDamage", 0x489280:"DamageArea", 0x701900:"ReceiveDamage",
 0x466380:"BulletClass ctor", 0x4664C0:"BulletClass Construct",
 0x4666E0:"BulletClass AI", 0x468D80:"Bullet Fire(hit)", 0x4690B0:"Detonate",
 0x6FDD50:"Techno Fire", 0x7730D0:"Weapon GetSize", 0x75E4F0:"Warhead GetSize",
 0x46C860:"BulletType GetSize", 0x46B540:"Bullet GetSize",
 0x7730E0:"Weapon WhatAmI",0x75E500:"Warhead WhatAmI",
 0x75CEC0:"Warhead ctor", 0x771C70:"Weapon ctor", 0x46BBC0:"BulletType ctor",
 0x75DE00:"?Verses loader region", 0x75DE48:"fstp in loader",
}
print("addr       tag                  coverage(sub/name/grade)                 atlas(size)")
for a,tag in sorted(KEY.items()):
    k=norm(f"{a:08X}")
    c=cov.get(k); at=atl.get(k)
    cs = f"{c['subsystem']}/{c['name']}/{c['grade']}" if c else "NOT-IN-COV"
    ats = f"size={at['size']}" if at else "NOT-IN-ATLAS"
    print(f"{a:08X}  {tag:<22} {cs:<48} {ats}")

# Locate Verses loader entry: scan backwards from 0x75DDE6 for a ret+nop boundary
print("\n=== scan backwards from 0x75DDC0 for function entry (ret/int3 + nops) ===")
for va in range(0x75DD80, 0x75DDE0):
    b=R.read(va,16)
    if b[:1]==b"\xc3" and b[1:5]==b"\x90\x90\x90\x90":
        print(f"  candidate entry @0x{va+5:X} (prev ret@0x{va:X}+4 nops)")
print("--- dump 0x75DD40..0x75DDC0 ---")
print(R.dump(0x75DD40,0x80))
