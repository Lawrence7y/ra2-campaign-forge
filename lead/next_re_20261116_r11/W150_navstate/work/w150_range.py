#!/usr/bin/env python3
"""W150: list function-atlas entries whose entry lies in one or more ranges.

Used to identify code that Ghidra left outside any defined function
(e.g. 0x5EF720, 0x7778CE) by showing the nearest entries around it.
"""
import sys

A = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
S = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W131_subsystems\fn_subsystem_canonical.tsv"

RANGES = [(0x5EF000, 0x5F0200), (0x777600, 0x777B00), (0x67E000, 0x67E600),
          (0x510F00, 0x512900), (0x81D400, 0x81D600)]

rows = []
for line in open(A, encoding="latin-1"):
    p = line.rstrip("\n").split("\t")
    if len(p) < 9:
        continue
    try:
        e = int(p[0], 16)
        sz = int(p[1])
    except ValueError:
        continue
    rows.append((e, sz, p[3], p[6], p[8] if len(p) > 8 else ""))

subs = {}
for line in open(S, encoding="latin-1"):
    p = line.rstrip("\n").split("\t")
    if len(p) < 4:
        continue
    try:
        subs[int(p[0], 16)] = p[2]
    except ValueError:
        pass

if len(sys.argv) > 1:
    RANGES = []
    for a in sys.argv[1:]:
        lo, hi = a.split("-")
        RANGES.append((int(lo, 16), int(hi, 16)))

for lo, hi in RANGES:
    print(f"=== functions with entry in [0x{lo:08X},0x{hi:08X}) ===")
    for e, sz, nc, fi, st in rows:
        if lo <= e < hi:
            print(f"  0x{e:08X} sz={sz:5d} end=0x{e+sz:08X} nc={nc:>3} "
                  f"sub={subs.get(e,'-'):22s} str={st[:160]}")
    print()
