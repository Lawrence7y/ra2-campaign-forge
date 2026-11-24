# -*- coding: utf-8 -*-
"""Dump full rows for NEW entries, and distinct grade/sub values across all deltas."""
import csv, os, sys, glob, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    try: return "%08X"%int(e,16)
    except: return e
cov={ne(r[0]):r for r in rd(os.path.join(ROOT,"COVERAGE","coverage.tsv"))[1:]}

grades=collections.Counter(); subs=collections.Counter(); hdrs=collections.Counter()
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    rows=rd(dpath); hdrs[tuple(rows[0])]+=1
    for r in rows[1:]:
        if not r or not r[0].strip(): continue
        if len(r)>4: grades[r[4].strip()]+=1
        if len(r)>1: subs[r[1].strip()]+=1
print("HEADERS:")
for h,c in hdrs.items(): print("  x%d %s"%(c,h))
print("\nDISTINCT GRADES:")
for g,c in grades.most_common(): print("  %-16r %d"%(g,c))
print("\nDISTINCT SUBSYSTEMS (non S\\d\\d):")
for s,c in subs.most_common():
    import re
    if not re.match(r"^S\d\d$",s): print("  %-20r %d"%(s,c))

print("\n\n=== ALL NEW ENTRY ROWS (entry not in coverage) ===\n")
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    card=os.path.basename(os.path.dirname(dpath))
    newrows=[r for r in rd(dpath)[1:] if r and r[0].strip() and ne(r[0]) not in cov]
    if not newrows: continue
    print("\n--- %s (%d NEW) ---"%(card,len(newrows)))
    for r in newrows:
        print("  | ".join(x.strip() for x in r[:6]))
