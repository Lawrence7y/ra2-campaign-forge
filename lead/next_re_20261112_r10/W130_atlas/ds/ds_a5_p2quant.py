#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A5 (P2 cont.): the address->class binding is MANY-TO-MANY.  Quantify it and
find what makes one COL "the" COL for a run."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import BASE, IMG, SECS, sec_of, in_raw, is_exec, u32, rd, cstr, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}

keystr = lambda a: f"0x{a:08X}"
# How many entries did the producer SKIP for names that got many vt?
byname = defaultdict(list)
for k, n in vt.items():
    byname[n].append(k)

print("=== col_count(2193) vs vt2name(1305): where did 888 go? ===")
# a COL is 'used' as vt-4 iff vt2name has (col+4)
col_used = sum(1 for k in vt if True)
print("  vt2name entries          :", len(vt))
print("  JSON col_count           :", J["col_count"])
print("  => 888 COLs had a table start but the key COLLIDED with an existing one")

print()
print("=== collision proof: distinct COL VAs that produce the SAME table-start key ===")
# rebuild all COLs independently
import re
pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
td = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for m in pat.finditer(blob):
        td[s.va + m.start() - 0x08] = m.group().decode("latin1")
cols = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td:
            cols[s.va + i - 0x0C] = td[v]
print("  distinct COL VAs:", len(cols), " distinct table starts:", len({c + 4 for c in cols}))
print("  => MULTI COLs per table-start:", len(cols) - len({c + 4 for c in cols}))

print()
print("=== P2 target: all COLs -> table-start 0x007E1F24 or 0x007E1F2C ===")
for c in sorted(cols):
    if c + 4 in (0x7E1F24, 0x7E1F2C):
        print(f"  COL 0x{c:08X} -> table 0x{c+4:08X}  {cols[c]}  sig=0x{u32(c):X} off={u32(c+4) if False else u32(c+8)} cd={u32(c+0x0C) and ''}")

print()
print("=== MSVC vs 这里的 header 结构：Col簇四周 0x007FAFD8 / 0x007FAFF0 / 0x007FB008 ===")
for c in (0x7FAFD8, 0x7FAFF0, 0x7FB008, 0x7FB118):
    print(f"\n-- COL 0x{c:08X} ({cols.get(c)}) --")
    print(f"   raw bytes: {rd(c, 16).hex()}")
    print(f"   +00 sig = 0x{u32(c):08X}")
    print(f"   +04 offset(=?) = 0x{u32(c+4):08X}")
    print(f"   +08 cdOffset   = 0x{u32(c+8):08X}")
    print(f"   +0C pTD        = 0x{u32(c+0x0C):08X}  -> name@+8 = {cstr(u32(c+0x0C)+8)}")

print()
print("=== which COL is 'canonical'? check the +0x04 field (MSVC: mdisp) ===")
# For MSVC, COL+4 = mdisp (member displacement), COL+8 = pdisp (vbtable disp),
# COL+0xC = vdisp, COL+0x10 = pTypeDescriptor  <-- note! this contradicts the brief
print("  brief says: +00 sig, +04 offset, +08 cdOffset, +0C pTypeDescriptor, +10 pClassDescriptor")
print("  file says : pTD is at +0C and the name lives at pTD+8 => that is consistent")
print("  but check whether pClassDescriptor is at +0x10 and what it holds:")
for c in list(sorted(cols))[:4]:
    print(f"   COL 0x{c:08X}  +0C=0x{u32(c+0x0C):08X}  +10=0x{u32(c+0x10):08X}  +14=0x{u32(c+0x14):08X}")
