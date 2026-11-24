#!/usr/bin/env python3
"""Count grade distribution per card and verify exact grade strings."""
import os
from collections import Counter
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
for n in range(1,11):
    card=f"C{n:02d}"
    p=os.path.join(ROOT,f"{card}_census","coverage_delta.tsv")
    grades=Counter()
    for line in open(p,encoding='utf-8',errors='replace'):
        parts=line.rstrip('\n').split('\t')
        if len(parts)<5 or parts[0]=='entry': continue
        grades[parts[4]]+=1
    print(f"{card}:")
    for g,c in grades.most_common():
        print(f"    {g!r} = {c}")
