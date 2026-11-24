#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A8: nail the exact 888 relationship.  col_va = pTD_slot_va - 0x0C, so key =
col_va+4 = pTD_slot_va - 8.  Find what addresses equal pTD_slot_va-8."""
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

# candidate COL VAs (aligned pTD dw)
cands = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td_set:
            cands[s.va + i] = s.va + i - 0x0C   # pTD_slot_va -> col_va

print("pTD slot VAs:", len(cands))
k = [(slot, cands[slot], cands[slot] + 4) for slot in cands]
in_keys = Counter((c + 4) in keys for _, c, _ in k)
print("  cand+4 in keys:", dict(in_keys))

print()
print("=== Where do 1305 COLs actually come from?  recompute the true COL set behind keys ===")
behind = {}
for key in keys:
    v = u32(key - 4)
    behind[key] = v
print("  all (key-4) values are COL VAs? ", all(v in cands.values() for v in behind.values()))
print("  distinct (key-4) :", len(set(behind.values())))

print()
print("=== For each key, the pTD slot VA; is pTD slot itself a key or key+4? ===")
rel = Counter()
for key, col in behind.items():
    slot = col + 0x0C
    rel[(slot - key)] += 1
print("  slot - key distribution:", dict(rel))

print()
print("=== RESOLVED: 888 unkeyed candidates = COLs whose col+4 is not a table start")
print("    i.e. those COL pointers sit in IMMEDIATE/code/data positions, not in a [vt-4] header.")
nl = [c for c in cands.values() if c + 4 not in keys]
print("  unkeyed candidate COLs:", len(nl), " keyed:", len(cands) - len(nl))
print("  by section of col_va:", dict(Counter(secname(c) for c in nl)))
# These unkeyed ones: is u32(col_va) small (real MSVC sig) or garbage?
sigv = Counter()
for c in nl:
    v = u32(c)
    sigv["0" if v == 0 else ("-1" if v == 0xFFFFFFFF else "other")] += 1
print("  unkeyed COL sig class:", dict(sigv))
sigv2 = Counter()
for c in cands.values():
    if c + 4 in keys:
        v = u32(c)
        sigv2["0" if v == 0 else ("-1" if v == 0xFFFFFFFF else "other")] += 1
print("  KEYED   COL sig class:", dict(sigv2))

print()
print("=== so: does 'sig' discriminate a real COL? ===")
print("  KEYED COLs with sig==0 or ==-1:", sum(v for kk, v in sigv2.items() if kk in ("0", "-1")),
      "/", sum(sigv2.values()))
print("  UNKEYED COLs with sig==0 or ==-1:", sum(v for kk, v in sigv.items() if kk in ("0", "-1")),
      "/", sum(sigv.values()))

print()
print("=== verify: for the 7 .text candidates, are they inside code? ===")
for c in sorted(x for x in cands.values() if secname(x) == ".text"):
    print(f"  col 0x{c:08X} name={td[u32(c+0x0C)]:<40} slot_va=0x{c+0x0C:08X} "
          f"u32(col)=0x{u32(c):08X} ctx={rd(c-6,14).hex()}")

print()
print("=== inverse check: every rsrc key ===")
for key, n in vt.items():
    if secname(key) == ".rsrc":
        print(f"  key=0x{key:08X} sec={secname(key)} name={n} col=0x{u32(key-4):08X} "
              f"col_sec={secname(u32(key-4))} sig=0x{u32(u32(key-4)):08X}")
        print(f"    bytes at key: {rd(key,16).hex()}")

print()
print("=== the 5 .data keys ===")
for key, n in vt.items():
    if secname(key) == ".data":
        c = u32(key - 4)
        print(f"  key=0x{key:08X} name={n:<40} col=0x{c:08X} sig=0x{u32(c):08X} "
              f"raw-bytes-at-key={in_raw(key)}")
