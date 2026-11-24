#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lookup coverage.tsv grade/semantics for a list of entries (batch helper)."""
import csv, os, sys
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
cov={}
with open(COV,encoding="utf-8") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        cov[row['entry'].strip().upper()]=row
entries=sys.argv[1:]
for e in entries:
    e=e.strip().upper()
    r=cov.get(e)
    if r:
        print("%s\t%s\t%s\t%s\t%s"%(e,r['subsystem'],r['grade'],r['name'],r['one_line_semantics'][:60]))
    else:
        print("%s\t-- NOT IN COVERAGE --"%e)
