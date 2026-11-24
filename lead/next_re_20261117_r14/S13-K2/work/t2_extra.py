#!/usr/bin/env python3
"""Evaluate extra proved candidates: (1) which atlas fn owns each of 9 Verses FPU consumers + grade;
   (2) factory push for Bomb/Parasite/RadSite slot12 sizes (dual-point closure)."""
import sys, os, csv, struct
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
cov={}; atl=[]
for r in csv.DictReader(open(COV,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("entry"): cov[int(r["entry"],16)]=r
for r in csv.DictReader(open(ATLAS,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("entry"): atl.append((int(r["entry"],16),int(r["size"])))
atl.sort()

def owner(addr):
    lo,hi=0,len(atl)-1; best=None
    for e,s in atl:
        if e<=addr<e+s: best=(e,s)
        if e>addr: break
    return best

print("=== 9 Verses FPU consumers: owning function + coverage grade ===")
for a in [0x48923D,0x6F36FE,0x6F3731,0x6F7D3D,0x6FCB6A,0x708AF7,0x70CEB2,0x70CEC7,0x70CF49]:
    o=owner(a)
    if o:
        e,s=o; c=cov.get(e)
        cs=f"{c['subsystem']}/{c['name']}/{c['grade']}" if c else "NOT-IN-COV"
        print(f"  consumer 0x{a:X} -> fn 0x{e:X}+{s:X}  {cs}")
    else:
        print(f"  consumer 0x{a:X} -> NO ATLAS OWNER")

print("\n=== factory push -> new for Bomb(0x5C)/Parasite(0x58)/RadSite(0x74) slot12 ===")
new_addr=0x7C8E17
text_start, text_end = 0x401000, 0x401000+0x3DF38D
o0=R.va_to_off(text_start); o1=R.va_to_off(text_end)
data=R.DATA
targets={0x5C:"BombClass size",0x58:"ParasiteClass size",0x74:"RadSiteClass size"}
for i in range(o0,o1-4):
    if data[i]==0xE8:
        rel=struct.unpack("<i",data[i+1:i+5])[0]
        cs=R.IB+0x1000+(i-o0)
        if cs+5+rel==new_addr:
            for back in (2,5,7):
                va=cs-back
                b=R.read(va,back+1)
                imm=None
                if back==2 and R.u8(va)==0x6A: imm=R.u8(va+1)
                elif back==5 and R.u8(va)==0x68: imm=R.u32(va+1)
                elif back==7 and R.read(va,3)==b"\xc7\x04\x24": imm=R.u32(va+3)
                if imm in targets:
                    print(f"  {targets[imm]} push 0x{imm:X}@0x{va:X} -> new cs0x{cs:X}")
