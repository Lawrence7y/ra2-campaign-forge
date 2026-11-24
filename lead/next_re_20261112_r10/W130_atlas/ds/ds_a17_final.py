#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A17: final consolidations.
 (1) P1 mechanism: prove COLs 0x0080xxxx are reached ONLY as
     `push 0x80` / `mov eax,0x8000xx` immediates whose little-endian bytes read
     0x0080_00xx.  Count .text dwords in [0x00800000,0x00810000) that are NOT COLs.
 (2) BSS boundary: does .data really lack bytes past 0x0087E000?  (brief claims it)
 (3) the 3 BSS-pointing keys whose +0x2C lands >= 0x0087E000.
"""
from __future__ import annotations
import json
from collections import Counter
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

t = next(s for s in SECS if s.name == ".text")
blob = IMG[t.va - BASE: t.va - BASE + t.vsize]
hits = []
for i in range(0, len(blob) - 4, 4):
    v = int.from_bytes(blob[i:i + 4], "little")
    if 0x00800000 <= v < 0x00810000:
        hits.append((t.va + i, v, v in td_set))
print("=== (1) .text aligned dwords in 0x00800000..0x0080FFFF ===")
# the producer invents a COL at value-0x0C.  For that fabricated COL,
#   pTD must sit at (value-0x0C)+0x0C == value
# so a .text dword V in 0x0080xxxx becomes a 'COL' IFF its own value is a real pTD!
orig = []
for i in range(0, len(blob) - 4, 4):
    v = int.from_bytes(blob[i:i + 4], "little")
    if 0x00800000 <= v < 0x00810000:
        orig.append((t.va + i, v))
print("  .text aligned dwords in that window:", len(orig))
print("  of which the dword ITSELF is a pTD (=> producer fabricates COL = value-0x0C):",
      sum(1 for _, v in orig if v in td_set))
print("  => the fabricated COL is always `immediate - 0x0C`, i.e. 0x007FFxxx")
from collections import defaultdict
cols_from_text = Counter()
for a, v in orig:
    if v in td_set:
        cols_from_text[v - 0x0C] += 1
print("   distinct synthetic COLs:", len(cols_from_text))
for c, n in cols_from_text.most_common():
    print(f"     synth COL 0x{c:08X}  (pTD 0x{c + 0x0C:08X} = {td_set and td.get(c + 0x0C)})  x{n}")

print()
print("  Are those synthetic COLs REAL .rdata COLs? (sig must be 0 or -1)")
for c in sorted(cols_from_text):
    sig = u32(c)
    print(f"     0x{c:08X} sig=0x{sig:08X} real COL={sig in (0, 0xFFFFFFFF)}")

print()
print("=== (2) .data raw coverage vs brief's claim ===")
d = next(s for s in SECS if s.name == ".data")
print(f"  .data va=0x{d.va:08X} vsize=0x{d.vsize:X} rawsize=0x{d.rsize:X}")
print(f"  => file bytes cover 0x{d.va:08X}..0x{d.va + d.rsize:08X}")
print(f"  brief claims coverage to 0x0087E000 : {d.va + d.rsize == 0x87E000}")
print(f"  BSS (no file bytes): 0x{d.va + d.rsize:08X}..0x{d.va + d.vsize:08X} "
      f"({d.vsize - d.rsize} bytes)")
print(f"  last 16 file bytes of .data: {rd(d.va + d.rsize - 16, 16).hex()}")
print(f"  first 16 at 0x0087E000 (in_raw={in_raw(0x87E000)}): "
      f"{rd(0x87E000,16) if in_raw(0x87E000) else 'NO BYTES (zero-fill)'}")

print()
print("=== (3) keys whose +0x2C lands in real .data BSS (>=0x0087E000) ===")
n = 0
for k, nm in vt.items():
    f = u32(k + 0x2C)
    if f and not in_raw(f) and 0x0087E000 <= f < 0x00B7A000:
        print(f"  key=0x{k:08X} {nm:<40} +2C=0x{f:08X} (BSS, would be 0 at runtime)")
        n += 1
print("  count:", n)

print()
print("=== (4) WhatAmI slot for the 87 .text keys: how many 'land in next table' ===")
print("   (already shown: 55 target BSS, 32 target a COL header, 0 genuine)")
c = Counter()
for k in vt:
    if secname(k) != ".text":
        continue
    f = u32(k + 0x2C)
    if f is None:
        c["unreadable"] += 1
    elif not in_raw(f):
        c["BSS"] += 1
    elif not is_exec(f):
        c["data (COL header)"] += 1
    else:
        b = rd(f, 6)
        c["mov-eax-ret" if (b[0] == 0xB8 and b[5] in (0xC3, 0xC2)) else "method"] += 1
print("  ", dict(c))
