#!/usr/bin/env python3
"""T2 evidence: (1) all FPU ops with SIB scale=8 disp=0xA0 (Verses consumers);
   (2) loader function entry boundary; (3) S13 sub_ naming candidates."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R
from capstone.x86 import X86_OP_MEM

print("=== all FPU mem ops with scale=8 disp=0xA0 (Verses consumers) ===")
text_start, text_end = 0x401000, 0x401000+0x3DF38D
code = R.read(text_start, text_end-text_start)
cnt=0
for ins in R.md.disasm(code, text_start):
    try:
        ops = ins.operands
    except Exception:
        continue  # skipdata padding (CS_ERR_SKIPDATA)
    for op in ops:
        if op.type==X86_OP_MEM and op.mem.scale==8 and op.mem.disp==0xA0:
            print(f"  {ins.address:08X} {ins.bytes.hex():<16} {ins.mnemonic} {ins.op_str}")
            cnt+=1
            break
print("  total:",cnt)

print("\n=== boundary around Verses loader (ret/int3 followed by nops) 0x75DC80..0x75DE10 ===")
for va in range(0x75DC80, 0x75DE10):
    b=R.read(va,2)
    if not b: continue
    if b[0] in (0xC3,0xC2,0xCC):
        nb=R.read(va+1,8)
        if nb and nb[0] in (0x90,0xCC):
            n=0
            for x in nb:
                if x in (0x90,0xCC): n+=1
                else: break
            if n>=4:
                print(f"  boundary ret/int3@0x{va:X} + {n} fill -> entry@0x{va+1+n:X}")

ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
subs=[]
for r in csv.DictReader(open(COV,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("subsystem")=="S13" and r.get("grade")!="[已证]" and r.get("name","").startswith("sub_"):
        subs.append((r["entry"],r["name"],r.get("one_line_semantics","")))
print(f"\n=== S13 non-proved sub_ entries: {len(subs)} (first 40) ===")
for e,n,s in subs[:40]:
    print(f"  {e} {n:<20} {s[:50]}")
