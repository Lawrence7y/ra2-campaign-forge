#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A12: the 286 .rdata targets -- are they table HEADERS ([vt-4] COL / [vt-0]
dword) of a DIFFERENT abutting table?  Walk the .rdata vt region as a sequence."""
from __future__ import annotations
import json
from collections import Counter
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd as rdb, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
keys = set(vt)
cols = {u32(k - 4) for k in keys}

# region: .rdata tables
rdkeys = [k for k in keys if secname(k) == ".rdata"]
print("keys in .rdata:", len(rdkeys), " min=0x%08X max=0x%08X" % (min(rdkeys), max(rdkeys)))

def slotstate(va):
    v = u32(va + 0x2C)
    if v is None: return "unreadable", v
    if v == 0: return "NULL", v
    if not in_raw(v): return "BSS", v
    if is_exec(v):
        b = rdb(v, 6)
        if b[0] == 0xB8 and b[5] in (0xC3, 0xC2): return "WhatAmI", v
        return "method", v
    if secname(v) == ".rdata":
        # classify the .rdata target precisely
        if v in cols:
            return "nextCOL", v
        if (v + 4) in keys:
            return "nextTableStart", v
        if u32(v) is not None and u32(v) in cols:
            return "COLptr", v
        return "rdata-other", v
    return "data-"+secname(v), v

cls = Counter()
byc = {}
for k, n in vt.items():
    c, f = slotstate(k)
    cls[c] += 1
    byc.setdefault(c, []).append((k, n, f))
print()
print("=== refined P3 classification ===")
for c, v in cls.most_common():
    print(f"  {c:<16}{v}")

print()
print("=== the 286: what EXACTLY is u32(key+0x2C)? ===")
sub = byc.get("nextCOL", []) + byc.get("nextTableStart", []) + byc.get("COLptr", []) + byc.get("rdata-other", [])
c2 = Counter(slotstate(k)[0] for k, n, f in byc.get("rdata-other", []))
print("  breakdown:", dict(cls))
print()
print("  witnesses: is the .rdata target the [vt-0] dword of an abutting table?")
for k, n, f in sub[:20]:
    # Is f immediately followed by a table start?
    nxt = f + 0x04
    print(f"    key=0x{k:08X} {n[:34]:<34} +2C=0x{f:08X}  "
          f"[f] is COL={f in cols}  f+4 is a table={nxt in keys}  "
          f"f itself is table={f in keys}  state={slotstate(k)[0]}")

print()
print("=== DEFINITIVE: reconstruct .rdata table layout linearly ===")
# All .rdata table starts, sorted, with their lengths
starts = sorted(k for k in keys if secname(k) == ".rdata")
print("  n=", len(starts))
gaps = Counter()
for i in range(len(starts) - 1):
    gaps[(starts[i + 1] - starts[i]) // 4] += 1
print("  inter-table distance (slots), top 15:", gaps.most_common(15))

print()
print("=== for each table, does +0x2C land in the NEXT table? (numeric proof) ===")
import bisect
res = Counter()
for k, n in vt.items():
    t = k + 0x2C
    i = bisect.bisect_right(starts, t) - 1
    if i < 0:
        res["before first table"] += 1
        continue
    host = starts[i]
    off = t - host
    res[f"inside table at +0x{off:X}"] += 1
print("  ", dict(sorted(res.items(), key=lambda x: -x[1])[:12]))

print()
print("=== sanity: for the 185 WhatAmI, is +0x2C inside its OWN table? ===")
own = 0
for k, n in vt.items():
    if slotstate(k)[0] != "WhatAmI":
        continue
    t = k + 0x2C
    i = bisect.bisect_right(starts, t) - 1
    if i >= 0 and starts[i] == k:
        own += 1
print(f"  {own}/185 land inside their own table (offset +0x2C from its start)")

print()
print("=== VERDICT evidence: 185 WhatAmI keys' N values ===")
vals = Counter()
for k, n in vt.items():
    c, f = slotstate(k)
    if c != "WhatAmI":
        continue
    vals[int.from_bytes(rdb(f + 1, 4), "little")] += 1
print("  distinct N:", len(vals), " range:", min(vals), "..", max(vals))
print("  N values < 200:", sorted(x for x in vals if x < 200))


