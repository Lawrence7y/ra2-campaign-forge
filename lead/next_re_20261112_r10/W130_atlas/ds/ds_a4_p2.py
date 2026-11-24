#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A4 (P2): is a remembered vt address the COL (vt-4) or the table?  Look at
0x007E1F24 vs 0x007E1F2C, then measure the systematic offset over all 1305."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import BASE, IMG, SECS, sec_of, in_raw, is_exec, u32, rd, cstr, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}

import re
pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
td = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for m in pat.finditer(blob):
        td[s.va + m.start() - 0x08] = m.group().decode("latin1")

RVA = {}

def name_of_col(cva):
    """resolve a COL va -> (name, td_va, sig, off, cd) or None if not a COL."""
    tdv = u32(cva + 0x0C)
    if tdv is None or tdv not in td:
        return None
    return (td[tdv], tdv, u32(cva), u32(cva + 4), u32(cva + 8))

print("=== P2: window 0x007E1F00..0x007E1F50 raw dwords ===")
print(f"{'addr':<12}{'dword':<12}{'as COL?':<46}as slot-target-sec")
for a in range(0x7E1F00, 0x7E1F50, 4):
    d = u32(a)
    r = name_of_col(d) if d else None
    coltxt = ""
    if r:
        coltxt = f"COL->{r[0]} (sig={r[2]:#x} off={r[3]} cd={r[4]})"
    print(f"0x{a:08X}  0x{d:08X}  {coltxt:<46}{secname(d)}")

print()
print("=== dwords FROM 0x007E1F24 and FROM 0x007E1F2C, with COL/exec annotation ===")
for base in (0x7E1F24, 0x7E1F2C):
    print(f"\n-- base 0x{base:08X}  (json says {vt.get(base)}) --")
    print(f"{'slot':<7}{'addr':<12}{'value':<12}{'sec':<12}{'exec':<6}{'as COL?'}")
    for i in range(-2, 14):
        a = base + 4 * i
        d = u32(a)
        r = name_of_col(d) if d else None
        print(f"{i:<7}0x{a:08X}  0x{d:08X}  {secname(d):<12}{str(is_exec(d)):<6}"
              f"{(r[0] + '  sig=' + hex(r[2])) if r else ''}")

print()
print("=== hypothesis test: is json[k] == name(COL at k) i.e. k is a COL, not a table? ===")
cat = Counter()
off_hist = Counter()     # (k) - (COL of k's own class furthest match) ... we test k itself
is_col = 0
is_table = 0
neither = 0
tbl_examples = []
for k, name in vt.items():
    r = name_of_col(k)
    if r and r[0] == name:
        is_col += 1
        cat["k is a COL with matching name"] += 1
        continue
    # is k a table (k-4 is a COL)?
    r2 = name_of_col(u32(k - 4)) if u32(k - 4) else None
    if r2 and r2[0] == name:
        is_table += 1
        cat["k is a TABLE (k-4 is COL)"] += 1
        tbl_examples.append(k)
        continue
    cat["neither"] += 1
    neither += 1
print("  ", dict(cat))

print()
print("=== so: for entries where k IS a COL, where is the real table? ===")
print("   (table = first address T such that T-4 is a COL for the class, T>k)")

# Build a full COL index over every section (aligned dword == TD-pTR position)
col_map = {}
for s in SECS:
    blob = IMG[s.va - BASE: s.va - BASE + s.rsize]
    for i in range(0, len(blob) - 4, 4):
        v = int.from_bytes(blob[i:i + 4], "little")
        if v in td:
            cva = s.va + i - 0x0C
            col_map[cva] = td[v]
print("  total COL candidates (any section, aligned):", len(col_map))
sigc = Counter(u32(c) for c in col_map)
print("  COL+0x00 signature == 0 :", sigc.get(0, 0), "  == 0xFFFFFFFF:",
      sigc.get(0xFFFFFFFF, 0), "  other:", len(col_map) - sigc.get(0, 0) - sigc.get(0xFFFFFFFF, 0))

# header-slot chain analysis: a real MSVC .rdata vt layout is
#   [vt-4]=COL, [vt-0]=dword (COL or 0), [vt+0]=first method...
print()
print("=== MSVC vt-in-thunk / COL-cluster structure around 0x007E1F24 ===")
for a in range(0x7E1EF0, 0x7E1F60, 4):
    d = u32(a)
    tag = ""
    if d is not None and name_of_col(d):
        tag = " COL(" + name_of_col(d)[0] + ")"
    print(f"0x{a:08X}  0x{d:08X}  {secname(d):<10}{tag}")
