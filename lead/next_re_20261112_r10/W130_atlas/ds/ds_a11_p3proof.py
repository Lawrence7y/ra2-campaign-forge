#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A11 (P3, decisive): the 638 `other-code` are ORDINARY METHODS, and the 286
`.rdata` targets are the NEXT table's [vt-4] COL header seen through an over-short
table.  Prove by locating which COL/table owns each +0x2C word."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
keys = set(vt)
col_addr = {u32(k - 4) for k in keys}      # every COL the producer used

def slotstate(va):
    v = u32(va + 0x2C)
    if v is None:
        return "unreadable", v
    if v == 0:
        return "NULL", v
    if not in_raw(v):
        return "BSS/no-bytes", v
    if is_exec(v):
        b = rd(v, 6)
        if b[0] == 0xB8 and b[5] in (0xC3, 0xC2):
            return "WhatAmI", v
        return "method", v
    return f"data-{secname(v)}", v

print("=== A. the 638 'method' class: are they real prologues? show 10 witnesses ===")
meth = [(k, n, slotstate(k)[1]) for k, n in vt.items() if slotstate(k)[0] == "method"]
print(f"  n={len(meth)}")
for k, n, fn in meth[:10]:
    b = rd(fn, 12)
    print(f"  key=0x{k:08X} {n[:42]:<42} +2C=0x{fn:08X} bytes={b.hex()}")
    print(f"       next slot +30=0x{u32(k+0x30):08X} +34=0x{u32(k+0x34):08X} +38=0x{u32(k+0x38):08X}")

print()
print("=== B. the 286 data-.rdata targets: is u32(+0x2C) a COL that belongs to a NEIGHBOURING table? ===")
rdt = [(k, n, slotstate(k)[1]) for k, n in vt.items() if slotstate(k)[0] == "data-.rdata"]
print(f"  n={len(rdt)}")
hit_col = sum(1 for k, n, f in rdt if f in col_addr)
print(f"  of those, +0x2C value is one of the COLs used by this map: {hit_col}/{len(rdt)}")
print()
print("  witnesses (key, +0x2C value, is it a COL?, which class owns that COL, delta to that table):")
shown = 0
for k, n, f in rdt:
    if f not in col_addr:
        continue
    owner_tbl = f + 4
    print(f"    key=0x{k:08X} {n[:36]:<36} +2C=0x{f:08X} is COL -> table 0x{owner_tbl:08X} "
          f"({vt.get(owner_tbl, '?')})  delta={owner_tbl - k}")
    shown += 1
    if shown >= 12:
        break

print()
print("=== C. delta distribution: +0x2C COL table vs key ===")
dl = Counter()
for k, n, f in rdt:
    if f in col_addr:
        dl[f + 4 - k] += 1
print("  ", dict(dl.most_common(20)))

print()
print("=== D. BSS targets (134) split into legs ===")
bss = [(k, n, slotstate(k)[1]) for k, n in vt.items() if slotstate(k)[0] == "BSS/no-bytes"]
print(f"  n={len(bss)};  of which key in .text: {sum(1 for k, n, f in bss if secname(k)=='.text')}")
print("  value ranges:")
rng = Counter()
for k, n, f in bss:
    if 0x0087E000 <= f < 0x00B7A000:
        rng["in .data BSS (>=0x0087E000)"] += 1
    elif 0x00800000 <= f < 0x0087E000:
        rng["0x0080_0000..0x0087DFFF but no bytes?"] += 1
    else:
        rng[f">=0xB7A000 or low"] += 1
print("  ", dict(rng))

print()
print("=== E. cross-check: for the 185 WhatAmI, does +0x2C sit INSIDE a longer table? ===")
for i, (k, n, f) in enumerate([(k, n, slotstate(k)[1]) for k, n in vt.items()
                               if slotstate(k)[0] == "WhatAmI"][:8]):
    b = rd(f, 6)
    n_ = int.from_bytes(b[1:5], "little")
    print(f"  key=0x{k:08X} {n[:40]:<40} +2C=0x{f:08X} bytes={b.hex()} "
          f"mov eax,{n_} ret@0x{f+5:02X}")

print()
print("=== F. slot-count test redone: how long IS each table really? ===")
def tbl_len(k, limit=0x400):
    a = k
    while a < k + limit:
        v = u32(a)
        if v is None or v == 0 or not is_exec(v):
            return (a - k) // 4
        a += 4
    return limit // 4
L = {k: tbl_len(k) for k in vt}
w = [(k, n, L[k], slotstate(k)[0]) for k, n in vt.items()]
print("  length/slot0x2C vs WhatAmI parse:")
for c in ("WhatAmI", "method", "NULL", "data-.rdata", "BSS/no-bytes"):
    sub = [x for x in w if x[3] == c]
    if not sub:
        continue
    enough = sum(1 for x in sub if x[2] > 11)
    print(f"    {c:<16} n={len(sub):<5} tables longer than slot 11: {enough}"
          f"  median len={sorted(x[2] for x in sub)[len(sub)//2]}")
print()
print("  => among keys whose table is SHORTER than slot 11, WhatAmI parses?")
short = [x for x in w if x[2] <= 11]
print("     ", Counter(x[3] for x in short))
print("  => among keys whose table REACHES slot 11, WhatAmI parses?")
long_ = [x for x in w if x[2] > 11]
print("     ", Counter(x[3] for x in long_))
