# -*- coding: utf-8 -*-
"""List every delta file: row count, first 2 rows verbatim, whether first row is a header."""
import csv, os, sys, glob
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    card=os.path.basename(os.path.dirname(dpath))
    rows=rd(dpath)
    first=rows[0] if rows else []
    ishdr = (first and first[0].strip().lower() in ("entry","entry(hex8)"))
    print("%-16s rows=%-5d first_is_header=%s first0=%r" % (card,len(rows),ishdr,first[0] if first else ""))
    if not ishdr:
        print("      ROW0: %s" % " | ".join(x.strip() for x in first[:6]))
