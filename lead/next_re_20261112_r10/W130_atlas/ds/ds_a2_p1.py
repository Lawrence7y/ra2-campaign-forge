#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A2 (P1): what are the 87 .text addresses really?  For each, examine
[addr-4], slot layout, and trace the COL chain it was derived from."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import (BASE, IMG, RAW, SECS, sec_of, in_raw, is_exec, u32, cstr, rd,
                    secname)

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
text = sorted(a for a in vt if secname(a) == ".text")

# ---------- rebuild TD / COL tables from scratch (independent) ----------
import re
pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
td = {}           # TD VA -> name
per_sec = Counter()
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for m in pat.finditer(blob):
        name_va = s.va + m.start()
        td[name_va - 0x08] = m.group().decode("latin1")
        per_sec[s.name] += 1
print("TD scan per section:", dict(per_sec), "unique TD:", len(td))

td_set = set(td)
col = {}          # COL VA -> (TD VA, sig, off, cdoff)
col_hits = defaultdict(list)
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td_set:
            cva = s.va + i - 0x0C
            col[cva] = (v, u32(cva), u32(cva + 4), u32(cva + 8))
            col_hits[v].append(s.va + i)
print("COL count (pTD match anywhere):", len(col))
print("TD with >1 pTD reference     :", sum(1 for v, l in col_hits.items() if len(l) > 1))
# validate COL signature
sigc = Counter()
for cva, (p, sig, off, cdoff) in col.items():
    sigc[(secname(cva), sig)] += 1
print("COL signature histogram (sec, sig):", dict(sigc))

# ---------- the 87 .text entries ----------
print()
print("=== [addr-4] value for the 87 .text keys ===")
kinds = Counter()
rows = []
by_name = defaultdict(list)
for a in text:
    prev = u32(a - 4)
    tgt = in_raw(prev) if prev is not None else False
    ex = is_exec(prev) if prev is not None else False
    if prev in col:
        k = "COL in .text"
    elif prev is not None and in_raw(prev) and ex:
        k = "code-ish"
    else:
        k = f"other[{secname(prev) if prev else 'unmapped'}]"
    kinds[k] += 1
    rows.append((a, vt[a], prev, k))
    by_name[vt[a]].append(a)
print(dict(kinds))
print()
print(f"{'addr':<12}{'name':<52}{'[addr-4]':<12}{'kind':<16}{'sec[addr-4]'}")
for a, n, p, k in rows:
    print(f"0x{a:08X}  {n:<52}0x{p:08X}  {k:<16}{secname(p)}")

print()
print("=== do these 87 cover whole classes (i.e. every mention of the name is .text)? ===")
alladdrs = defaultdict(list)
for a, n in vt.items():
    alladdrs[n].append(a)
only_text = [n for n, l in alladdrs.items() if all(secname(x) == ".text" for x in l)]
mixed = [n for n, l in alladdrs.items() if any(secname(x) == ".text" for x in l) and any(secname(x) != ".text" for x in l)]
print("distinct names among 87 keys:", len(alladdrs and {vt[a] for a in text}))
print("names whose every key is .text:", len(only_text))
print("names that appear both in .text and elsewhere:", len(mixed))
for n in mixed[:20]:
    print("   ", n, [f"0x{x:08X}" for x in sorted(alladdrs[n])])

print()
print("=== numeric relation addr vs its (name's) real vtable ===")
rel = Counter()
for a, n, p, k in rows:
    others = [x for x in alladdrs[n] if secname(x) != ".text"]
    if not others:
        rel["no non-text sibling"] += 1
        continue
    for o in others:
        rel[o - a] += 1
print("delta = (non-text sibling) - (text addr):", dict(rel.most_common(12)))

print()
print("=== raw bytes at each .text addr (are we looking at code or at a pointer? ) ===")
for a, n, p, k in rows[:10]:
    print(f"0x{a:08X} {n:<45} -8..+16: {rd(a-8,24).hex()}")

open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\ds\ds_a2_p1.tsv",
     "w", encoding="utf-8").write(
    "addr\tname\tprev4\tkind\tsec_prev\n" +
    "\n".join(f"0x{a:08X}\t{n}\t0x{p:08X}\t{k}\t{secname(p)}" for a, n, p, k in rows))
print("\n[out] ds_a2_p1.tsv")
