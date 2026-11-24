#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p

CAND = [
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
]
CSET = set(CAND)

print("=== EVENT L1 table @ 0x71F218 (12 dwords) ===")
for i in range(12):
    v = p.dword_va(0x71F218 + 4*i)
    mark = " <== CANDIDATE" if v in CSET else ""
    print(f"L1[{i:2d}] = 0x{v:08X}{mark}")

print()
print("=== EVENT L2 table @ 0x71F248 (49 bytes) ===")
vals = [p.byte_va(0x71F248+i) for i in range(49)]
print("values:", ' '.join(f"{v:02X}" for v in vals))
print("distinct:", sorted(set(vals)))

print()
print("=== dispatch insn @ 0x71E940..0x71E980 ===")
for insn in p.disasm(0x71E940, 0x40):
    print(p.fmt(insn))

print()
print("=== ACTION jump table @ 0x6DFDEC (145 dwords) ===")
act = []
for i in range(145):
    v = p.dword_va(0x6DFDEC + 4*i)
    act.append(v)
    mark = " <== CANDIDATE" if v in CSET else ""
    print(f"ACT[{i:3d}] (ID {i+1:3d}) = 0x{v:08X}{mark}")

print()
print("=== candidates that appear in EVENT L1 ===")
l1 = [p.dword_va(0x71F218+4*i) for i in range(12)]
for c in CAND:
    if c in l1:
        print(f"0x{c:08X} at L1 index {l1.index(c)}")

print()
print("=== candidates that appear in ACTION table ===")
for c in CAND:
    if c in act:
        idx = [i for i,v in enumerate(act) if v==c]
        print(f"0x{c:08X} at ACT indices {[i+1 for i in idx]} (IDs)")
