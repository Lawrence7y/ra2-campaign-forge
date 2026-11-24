#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
ROOT = r"D:\Project\ra2-campaign-forge"
COV  = ROOT + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL  = ROOT + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

atlas=set()
with open(ATL,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        atlas.add((r['entry'] or '').strip().lower())

rows=[]
with open(COV,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if (r['subsystem'] or '').strip()=='S15' and (r['entry'] or '').strip().lower() in atlas:
            rows.append(r)
rows.sort(key=lambda x:x['entry'])
for r in rows:
    print(f"{r['entry']}\t{r['grade']}\t{r['name']}\t{r['one_line_semantics']}")
