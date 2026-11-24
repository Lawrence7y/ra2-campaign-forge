#!/usr/bin/env python3
import csv, os
LEAD = r"D:\Project\ra2-campaign-forge\lead"
EP = os.path.join(LEAD, "next_re_20261117_r14", "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
VD = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID", "_verdicts.tsv")
def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))
ep = load(EP); vd = load(VD)
und = [r for r in ep if r["label"] == "UNDECIDED" and "EVIDENCE" in r["rel"]]
vdset = set(r["rel"] for r in vd)
undset = set(r["rel"] for r in und)
print("in vd not in und:")
for rel in sorted(vdset - undset):
    print("  VD:", repr(rel))
    # find in ep by rel
    for r in ep:
        if r["rel"] == rel:
            print("    EP label=", repr(r["label"]), "why=", repr(r["why"]), "bytes=", r["bytes"])
            break
    else:
        print("    NOT IN EP at all")
# Also check label values distribution for rows with EVIDENCE
from collections import Counter
print("labels with EVIDENCE path:", Counter(r["label"] for r in ep if "EVIDENCE" in r["rel"]))
print("UNDECIDED total:", sum(1 for r in ep if r["label"]=="UNDECIDED"))
print("UNDECIDED no EVIDENCE:", [r["rel"] for r in ep if r["label"]=="UNDECIDED" and "EVIDENCE" not in r["rel"]][:20])
