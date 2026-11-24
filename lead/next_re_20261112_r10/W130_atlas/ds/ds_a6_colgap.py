#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A6: settle the 2193-vs-1305 gap by RE-RUNNING the producer's three loops
instrumented, step for step.  Also classify every COL by signature."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
import re
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, cstr, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())

pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
td = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for m in pat.finditer(blob):
        td[s.va + m.start() - 0x08] = m.group().decode("latin1")
td_set = set(td)

# loop 2 exactly as producer: dict col2name[col_va] = td[v]
col2name = {}
col_write_count = 0
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td_set:
            cva = s.va + i - 0x0C
            if cva >= 0:
                if cva in col2name:
                    col_write_count += 1
                col2name[cva] = td[v]
print("loop2: COL hits:", len(col2name) + col_write_count, " unique COL VAs:", len(col2name),
      " overwritten:", col_write_count)

# loop 3 exactly as producer: dict vt2name[va+4] = col2name[v]
vt2 = {}
vt_writes = 0
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in col2name:
            k = s.va + i + 4
            if k in vt2:
                vt_writes += 1
            vt2[k] = col2name[v]
print("loop3: writes:", len(vt2) + vt_writes, " unique keys:", len(vt2), " overwritten:", vt_writes)
print("json len(vt2name):", len(J["vt2name"]), " match:", {f'0x{k:08X}': v for k, v in vt2.items()} == J["vt2name"])

# So: unique COL VAs (2193) but only 1305 unique (col+4) keys => collisions of col+4.
print()
print("=== collision check: how many COL VAs share the same (col+4)? ===")
shared = defaultdict(list)
for c in col2name:
    shared[c + 4].append(c)
multi = {k: v for k, v in shared.items() if len(v) > 1}
print("  distinct col+4 keys:", len(shared), " keys with >1 COL:", len(multi),
      " total COLs in them:", sum(len(v) for v in multi.values()))
for k in sorted(multi)[:6]:
    print(f"  table 0x{k:08X}:", [(f'0x{c:08X}', col2name[c]) for c in sorted(multi[k])])

print()
print("=== classify the 2193 COLs by (sec, sig) ===")
cat = Counter()
for c, n in col2name.items():
    sig = u32(c)
    sm = secname(c)
    if sm == ".rdata" and sig in (0, 0xFFFFFFFF):
        cat[f"{sm} sig={'0' if sig==0 else '-1'}"] += 1
    else:
        cat[f"{sm} sig=other"] += 1
for k, v in sorted(cat.items()):
    print(f"  {k:<22}{v}")

print()
print("=== the 'other sig' COLs: where are they and what are they really? ===")
other = [c for c in col2name if u32(c) not in (0, 0xFFFFFFFF)]
print("  count:", len(other))
print(f"{'COL va':<12}{'name':<48}{'sig':<12}{'sec':<8}{'selftable':<6}{'td+8 readable'}")
for c in sorted(other)[:20]:
    n = col2name[c]
    tdv = u32(c + 0x0C)
    print(f"0x{c:08X}  {n:<48}0x{u32(c):08X}  {secname(c):<8}"
          f"{str(not is_exec(c)):<6}{cstr(tdv + 8) is not None}")

print()
print("=== are those 'other sig' COLs self-consistent? (pTD at +0x0C pointing at a TD) ===")
ok = sum(1 for c in other if u32(c + 0x0C) in td_set)
print(f"  {ok}/{len(other)} have a valid pTD at +0x0C  => they ARE COLs, only signature byte differs")
#if sig != 0 that suggests our TD base is off, or these are in .text...
print()
print("=== distribution of `other` COLs by section ===")
print("  ", dict(Counter(secname(c) for c in other)))
print()
print("=== .text 'other-sig' COLs are the P1 false positives: list them ===")
print("  .text COLs:", sum(1 for c in col2name if secname(c) == '.text'))
print("  of which feed a .text table start:", sum(1 for a in J['vt2name'] if secname(int(a,16))=='.text'))
