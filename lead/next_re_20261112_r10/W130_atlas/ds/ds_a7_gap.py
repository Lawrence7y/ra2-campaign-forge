#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A7: 2193 candidates -> only 1305 keys.  Trace the 888 non-keys one by one."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
import re
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, cstr, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}

pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
td = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for m in pat.finditer(blob):
        td[s.va + m.start() - 0x08] = m.group().decode("latin1")
td_set = set(td)

cands = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td_set:
            cands[s.va + i - 0x0C] = (td[v], s.va + i)   # col_va -> (name, pTD_slot_va)

print("candidates:", len(cands))
keys = set(vt)

# for each candidate, does col_va+4 exist as a key?
hit = [c for c in cands if c + 4 in vt]
miss = [c for c in cands if c + 4 not in vt]
print("col+4 is a key:", len(hit), "   col+4 NOT a key:", len(miss))

print()
print("=== why do 888 candidates NOT produce a key?  the pTD slot is exactly a KEY address? ===")
# In loop 3 the scan is over the SAME set of dwords; a candidate at col_va means the
# pTD slot is at col_va+0x0C.  If col_va+4 is not a key, it means when the loop reached
# va = col_va+4-4 = col_va, the value stored there (u32(col_va)) was not a *unique* COL
# in col2name... but we showed it is.  So print u32(col_va) and check membership.
probe = Counter()
for c in miss[:0]:
    pass
for c in miss:
    v0 = u32(c)
    probe["u32(col) in col2name" if v0 in cands else "u32(col) NOT in col2name"] += 1
print(dict(probe))

print()
print("=== check: is col_va itself (as a key source) shadowed because u32(col_va) is a COL VA")
print("    that got OVERWRITTEN to another name?  compare names ===")
mismatch = 0
for c in hit:
    if cands[c][0] != vt[c + 4]:
        mismatch += 1
print("  hit & name mismatch:", mismatch, "/", len(hit))

print()
print("=== so the 888 must fail on  u32(col_va) in col2name ===")
cnt = Counter()
for c in miss:
    v0 = u32(c)
    cnt["u32(col) IS a COL VA" if (v0 in cands) else "u32(col) is NOT a COL VA"] += 1
print(" ", dict(cnt))

print()
print("=== sample of the 888 whose u32(col) is NOT a COL VA: what is u32(col)? ===")
ex = [c for c in miss if u32(c) not in cands][:15]
print(f"{'col va':<12}{'name':<46}{'u32(col)':<12}{'sec of u32':<12}{'is that its COL?'}")
for c in ex:
    v0 = u32(c)
    print(f"0x{c:08X}  {cands[c][0]:<46}0x{v0:08X}  {secname(v0):<12}")

print()
print("=== KEY INSIGHT TEST: what sits at col_va-8 / col_va-4 for a HIT vs a MISS? ===")
def show(c):
    return f"[{c-8:X}]={u32(c-8):08X} [{c-4:X}]={u32(c-4):08X} [col]={u32(c):08X} [+4]={u32(c+4):08X}"
print(" HIT  samples (col+4 is a key):")
for c in hit[:10]:
    print(f"  0x{c:08X} {cands[c][0][:34]:<34} {show(c)}")
print(" MISS samples (col+4 is NOT a key):")
for c in miss[:10]:
    print(f"  0x{c:08X} {cands[c][0][:34]:<34} {show(c)}")

print()
print("=== does .rdata contain a SECOND, denser COL array the producer also hit? ===")
print("  candidate COLs by sec:", dict(Counter(secname(c) for c in cands)))
print("  KEYS by sec        :", dict(Counter(secname(k) for k in keys)))

print()
print("=== PARTITION: among the 2193 candidates, which look like REAL MSVC COLs? ===")
# real COL heuristic: +4 (mdisp) and +8 (pdisp/vdisp) are small, and pTD at +0x0C
real = []
for c in sorted(cands):
    a = u32(c + 4)
    b = u32(c + 8)
    if a is not None and b is not None and (a & 0xFFFF0000) == 0 and (b & 0xFFFF0000) == 0:
        real.append(c)
print("  candidates with small +4 and +8 :", len(real))
print("  of those, col+4 is a key        :", sum(1 for c in real if c + 4 in vt))
print("  candidates FAILING that test     :", len(cands) - len(real),
      " of which col+4 is a key:", sum(1 for c in cands if c not in set(real) and c + 4 in vt))
