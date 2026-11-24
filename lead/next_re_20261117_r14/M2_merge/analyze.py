# -*- coding: utf-8 -*-
"""M2 T1 analysis — read-only. For every coverage_delta.tsv, classify each row vs coverage.tsv."""
import csv, os, sys, collections, glob, re

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")

def read_tsv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

def norm_entry(e):
    e = e.strip().upper()
    # hex normalize, pad to 8
    try:
        return "%08X" % int(e, 16)
    except Exception:
        return e

cov_rows = read_tsv(COV)[1:]
cov = {}
cov_dups = collections.Counter()
for r in cov_rows:
    e = norm_entry(r[0])
    cov_dups[e]+=1
    cov[e] = r  # last wins but we verified no dups

GRADE_RANK = {"[已证]":3, "[静态推断]":2, "[未证]":1}

# find all delta files
deltas = sorted(glob.glob(os.path.join(ROOT, "**", "coverage_delta.tsv"), recursive=True))
print("DELTA_FILES:", len(deltas))

summary = []
for dpath in deltas:
    card = os.path.basename(os.path.dirname(dpath))
    vpath = os.path.join(os.path.dirname(dpath), "_audit", "VERDICT.md")
    # verdict
    verdict = "NO_VERDICT"
    if os.path.exists(vpath):
        txt = open(vpath, encoding="utf-8-sig").read()
        # last occurrence of PASS/PARTIAL/FAIL near 裁决
        m = re.findall(r"裁决[：:]?\s*\*{0,2}\s*(PASS|PARTIAL|FAIL)", txt, re.I)
        if m:
            verdict = m[-1].upper()
        elif re.search(r"\*\*PASS\*\*|裁决.*PASS", txt, re.I):
            verdict = "PASS"
    rows = read_tsv(dpath)
    hdr = rows[0]
    drows = rows[1:]
    # count classification
    same=0; diffgrade=0; conflict=0; new=0
    new_samples=[]; diff_samples=[]; conflict_samples=[]
    seen_entries=set()
    for r in drows:
        if not r or not r[0].strip(): continue
        e = norm_entry(r[0])
        seen_entries.add(e)
        dsub = r[1].strip() if len(r)>1 else ""
        dname = r[2].strip() if len(r)>2 else ""
        dgrade = r[4].strip() if len(r)>4 else ""
        if e in cov:
            c = cov[e]
            csub = c[1].strip(); cname = c[2].strip(); cgrade = c[4].strip()
            # same value? grade & name (and subsystem)
            if dgrade==cgrade and dname==cname and dsub==csub:
                same+=1
            elif dgrade!=cgrade:
                diffgrade+=1
                if len(diff_samples)<8: diff_samples.append((e,cgrade,dgrade,cname,dname))
            else:
                # same grade, diff name or subsystem -> conflict
                conflict+=1
                if len(conflict_samples)<8: conflict_samples.append((e,csub+"/"+cname,dsub+"/"+dname))
        else:
            new+=1
            if len(new_samples)<12: new_samples.append((e,dsub,dname,dgrade))
    summary.append((card, verdict, len(drows), same, diffgrade, conflict, new, new_samples, diff_samples, conflict_samples))

print("\n%-18s %-10s %5s %5s %5s %5s %5s" % ("CARD","VERDICT","ROWS","SAME","DGRD","CONF","NEW"))
for s in summary:
    print("%-18s %-10s %5d %5d %5d %5d %5d" % (s[0],s[1],s[2],s[3],s[4],s[5],s[6]))

print("\n\n=== DETAIL: cards with NEW or DIFFGRADE or CONFLICT ===")
for s in summary:
    card,verdict,nrows,same,dgrd,conf,new,ns,ds,cs = s
    if new or dgrd or conf:
        print("\n--- %s (verdict=%s rows=%d same=%d dgrd=%d conf=%d new=%d) ---" % (card,verdict,nrows,same,dgrd,conf,new))
        if ns:
            print("  NEW samples (entry,sub,name,grade):")
            for x in ns: print("   ",x)
        if ds:
            print("  DIFF GRADE samples (entry,cov_grade,delta_grade,cov_name,delta_name):")
            for x in ds: print("   ",x)
        if cs:
            print("  CONFLICT samples (entry,cov(sub/name),delta(sub/name)):")
            for x in cs: print("   ",x)
