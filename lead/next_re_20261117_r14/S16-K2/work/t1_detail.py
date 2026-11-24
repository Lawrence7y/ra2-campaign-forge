#!/usr/bin/env python3
"""S16-K2: print detailed S16 target breakdown (UTF-8 safe)."""
import csv, os
ROOT = r"D:\Project\ra2-campaign-forge"
RAW = os.path.join(ROOT, r"lead\next_re_20261117_r14\S16-K2\work\t1_targets_raw.tsv")
rows = list(csv.DictReader(open(RAW, encoding="utf-8"), delimiter="\t"))

print("=== S16 IN ATLAS, UNNAMED (name is sub_ placeholder) ===")
un = [r for r in rows if r["in_atlas"]=="Y" and r["is_named_strict"]=="N"]
for r in un:
    print(f"{r['entry']}\t{r['grade']}\t{r['name']}\t{r['one_line_semantics'][:70]}")

print("\n=== S16 IN ATLAS, NOT PROVED (grade != [已证]) ===")
np_ = [r for r in rows if r["in_atlas"]=="Y" and r["is_proved"]=="N"]
for r in np_:
    print(f"{r['entry']}\t{r['grade']}\t{r['name']}\t{r['one_line_semantics'][:70]}")

print("\n=== S16 IN ATLAS, BOTH named+proved (already good) ===")
gp = [r for r in rows if r["in_atlas"]=="Y" and r["is_named_strict"]=="Y" and r["is_proved"]=="Y"]
print("count:", len(gp))

print("\n=== S16 IN ATLAS, named but NOT proved ===")
nq = [r for r in rows if r["in_atlas"]=="Y" and r["is_named_strict"]=="Y" and r["is_proved"]=="N"]
for r in nq:
    print(f"{r['entry']}\t{r['grade']}\t{r['name']}\t{r['one_line_semantics'][:70]}")

print("\n=== S16 OUT OF ATLAS ===")
for r in rows:
    if r["in_atlas"]=="N":
        print(f"{r['entry']}\t{r['grade']}\t{r['name']}\t{r['one_line_semantics'][:70]}")
