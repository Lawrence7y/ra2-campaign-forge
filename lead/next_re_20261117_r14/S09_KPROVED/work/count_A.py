#!/usr/bin/env python3
"""Independent recount of A set for S09: has4_strict=1 AND has2_rtti=1 (②∧④).
Also reports raw has4_strict=1 and the has2_rtti=0 subset. Read-only.
"""
import csv
CLASS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
rows=[r for r in csv.DictReader(open(CLASS,encoding='utf-8'),delimiter='\t') if r['subsystem']=='S09']
raw=[r for r in rows if r['has4_strict']=='1']
no2=[r for r in raw if r['has2_rtti']=='0']
a_set=[r for r in raw if r['has2_rtti']=='1']
print('S09 total =',len(rows))
print('has4_strict=1 (raw) =',len(raw))
print('  of which has2_rtti=0 (no ②, not in A) =',len(no2))
print('A set (has4_strict=1 AND has2_rtti=1) =',len(a_set))
assert len(raw)-len(no2)==len(a_set)
