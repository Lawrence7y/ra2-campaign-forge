#!/usr/bin/env python3
"""Final consistency check for S13-K2 deliverables (read-only)."""
import os, csv
ROOT=r"D:\Project\ra2-campaign-forge"
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S13-K2")
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
# delta path may have been misplaced; find it
delta_candidates=[]
for dp,dn,fn in os.walk(os.path.join(ROOT,"lead","next_re_20261117_r14")):
    for f in fn:
        if f=="coverage_delta.tsv" and "S13-K2" in dp:
            delta_candidates.append(os.path.join(dp,f))
print("delta files found:", delta_candidates)
delta=delta_candidates[0] if delta_candidates else None
# load coverage S13
cov={}
for r in csv.DictReader(open(COV,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("entry"): cov[r["entry"].strip().upper().zfill(8)]=r
# load TARGETS
tgt=set()
for r in csv.DictReader(open(os.path.join(CARD,"TARGETS.tsv"),encoding="utf-8",errors="replace"),delimiter="\t"):
    tgt.add(r["entry"].strip().upper().zfill(8))
print("TARGETS rows:",len(tgt))
if delta:
    rows=list(csv.reader(open(delta,encoding="utf-8"),delimiter="\t"))
    print("delta rows:",len(rows))
    ok=0
    for r in rows:
        if len(r)<6: print("  BAD ROW",r); continue
        e=r[0].strip().upper().zfill(8)
        c=cov.get(e)
        ev=os.path.join(ROOT,r[5])
        checks={
          "in_TARGETS": e in tgt,
          "cov_grade_未证": c and c["grade"]=="[未证]",
          "ev_exists": os.path.exists(ev),
          "sub_S13": r[1]=="S13",
          "grade_已证": r[4]=="[已证]",
        }
        good=all(checks.values())
        ok+=good
        print(f"  {e} {'OK' if good else 'FAIL '+str(checks)}  cov={c['grade'] if c else 'NA'}/{c['name'] if c else 'NA'}")
    print(f"delta valid rows: {ok}/{len(rows)}")
