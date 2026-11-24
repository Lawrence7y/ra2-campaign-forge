#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A9: clean re-derivation.  Verify producer's invariants directly, no guessing."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
import re
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, cstr, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
keys = set(vt)

pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
td = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for m in pat.finditer(blob):
        td[s.va + m.start() - 0x08] = m.group().decode("latin1")
td_set = set(td)
print("TD count:", len(td))

# ---- INVARIANT 1: every key has u32(key-4) that is a 'COL candidate' ----
# producer's col2name: col_va such that u32(col_va) in td_set AND col_va=slot-0x0C, col_va>=0
#   <=> u32(col_va) in td_set  (that's it; col_va >= 0 is always true here)
# So col2name = {c : u32(c) in td_set} for all aligned c  -- NOT necessarily c+0x0C
col2name = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td_set:
            cva = s.va + i - 0x0C
            col2name[cva] = td[v]
print("col2name size:", len(col2name), " (json col_count:", J["col_count"], ")")

# ---- INVARIANT 2: vt2name keys == {va+4 : u32(va) in col2name} ----
derived = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in col2name:
            derived[s.va + i + 4] = col2name[v]
print("derived keys:", len(derived), " identical to json:", derived == vt)

print()
print("=== CRITICAL: is pTD at col+0x0C for the KEYED COLs? ===")
okc = sum(1 for k in keys if u32(u32(k - 4) + 0x0C) in td_set)
print(f"  keys whose (key-4)+0x0C is a pTD : {okc}/{len(keys)}")
print("  => the 'COL' the producer uses is really 'the dword 4 bytes before the key', and")
print("     for these the +0x0C field happens to be the pTD. Check the offsets actually used:")

print()
print("=== re-derive with STRICT MSVC COL rule: u32(col+0x0C) in td_set AND sig in {0,-1} ===")
strict = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 16, 4):
        c = s.va + i
        v = u32(c + 0x0C)
        sig = u32(c)
        if v in td_set and sig in (0, 0xFFFFFFFF):
            strict[c] = td[v]
print("  strict COLs:", len(strict))

strict_keys = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in strict:
            strict_keys[s.va + i + 4] = (strict[v], v)
print("  strict table starts:", len(strict_keys))

print()
print("=== INTERSECTION / DIFF between producer keys and strict table starts ===")
print("  in both            :", len(keys & set(strict_keys)))
print("  producer-only      :", len(keys - set(strict_keys)))
print("  strict-only        :", len(set(strict_keys) - keys))
po = sorted(keys - set(strict_keys))
so = sorted(set(strict_keys) - keys)
print("  producer-only by sec:", dict(Counter(secname(a) for a in po)))
print("  strict-only   by sec:", dict(Counter(secname(a) for a in so)))
print()
print("  producer-only samples (key, [key-4], its sig, is (key-4)+0xC a pTD?):")
for k in po[:15]:
    c = u32(k - 4)
    print(f"    key=0x{k:08X} col=0x{c:08X} sig=0x{u32(c):08X} "
          f"ptd_at_+0C={u32(c+0x0C) in td_set} name={vt[k][:40]}")
print()
print("  strict-only samples:")
for k in so[:15]:
    print(f"    key=0x{k:08X} {strict_keys[k][0][:40]} col=0x{strict_keys[k][1]:08X}")
