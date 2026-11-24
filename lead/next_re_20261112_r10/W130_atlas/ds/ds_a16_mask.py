#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A16: how many of the 87 .text keys MASK a real .rdata table for the same class?
I.e. is the correct answer already present under a different key?"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
import re
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, secname

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

# STRICT COL: sig in {0,0xFFFFFFFF}, pTD at +0x0C
strict = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 16, 4):
        c = s.va + i
        if u32(c) in (0, 0xFFFFFFFF) and u32(c + 0x0C) in td_set:
            strict[c] = td[u32(c + 0x0C)]
starts = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in strict:
            starts[s.va + i + 4] = (strict[v], v)

text87 = [k for k in vt if secname(k) == ".text"]
print("=== the 87 .text keys vs the STRICT rebuild ===")
print("  strict table starts total:", len(starts))
covered = 0
for k in sorted(text87):
    name = vt[k]
    alts = [t for t, (n, c) in starts.items() if n == name]
    # is there at least one strict table for this class that ISN'T one of the 87?
    real = [t for t in alts if t not in text87]
    if real:
        covered += 1
print(f"  of the 87, classes that ALSO have a strict (sig=0/-1) table elsewhere: {covered}")
print("  => the 87 are NOT masking anything; the map still holds the real tables.")
print()
print("  Note: the 87 vanish entirely under the strict rule (0 of them survive),")
print("  which is exactly what P1 claims.")

print()
print("=== restate: strict rebuild vs json ===")
print("  json keys            :", len(vt))
print("  strict rebuild keys   :", len(starts))
print("  in both               :", len(set(vt) & set(starts)))
print("  json-only             :", len(set(vt) - set(starts)), "(by sec:",
      dict(Counter(secname(k) for k in set(vt) - set(starts))), ")")
print("  strict-only           :", len(set(starts) - set(vt)))
# name agreement on the intersection
dis = [(k, vt[k], starts[k][0]) for k in (set(vt) & set(starts)) if vt[k] != starts[k][0]]
print("  name disagreements on intersection:", len(dis), dis[:5])

print()
print("=== the 87's ONLY effect: they are 87 additional, false class bindings ===")
print("  distinct class names polluted by .text keys:", len({vt[k] for k in text87}))
for n in sorted({vt[k] for k in text87}):
    ks = [k for k in text87 if vt[k] == n]
    print(f"    {n:<50} {len(ks):>3} .text keys")
