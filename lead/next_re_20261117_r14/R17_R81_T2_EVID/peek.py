#!/usr/bin/env python3
"""按需 dump 指定 rel 的前 8KiB 前 40 行，供人工判读（不看 why 列）。"""
import csv, os, sys
LEAD = r"D:\Project\ra2-campaign-forge\lead"
UL = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID", "_undead_evid.tsv")
with open(UL, encoding="utf-8", newline="") as f:
    rows = {r["rel"]: r for r in csv.DictReader(f, delimiter="\t")}
keys = sys.argv[1:]
for k in keys:
    p = os.path.join(LEAD, k.replace("/", os.sep))
    print("="*100)
    print(k)
    if not os.path.exists(p):
        print("  MISSING"); continue
    with open(p, "rb") as fh:
        t = fh.read(8192).decode("utf-8", errors="replace")
    for i, l in enumerate(t.splitlines()[:40]):
        print(f"  {i+1:3d}| {l[:160]}")
