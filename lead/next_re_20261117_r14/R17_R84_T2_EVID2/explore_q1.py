#!/usr/bin/env python3
# R45-T2-EVID2 探查：验证 1242 = 976 + 266 的集合关系，看 266 件的 O/P/bnform/varatio 分布
# 只读 lead\；写只写本目录
import csv, os, collections

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R84_T2_EVID2")
EP = os.path.join(LEAD, "next_re_20261117_r14", "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
VD = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID", "_verdicts.tsv")
CM = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID", "_content_metrics.tsv")
UD = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID", "_undead_evid.tsv")

def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

ep = load(EP)
vd = load(VD)
cm = load(CM)
ud = load(UD)

# 1242: label=UNDECIDED and path contains EVIDENCE
und = [r for r in ep if r["label"] == "UNDECIDED" and "EVIDENCE" in r["rel"]]
print("EP rows", len(ep), "UNDECIDED&EVIDENCE", len(und),
      "bytes", sum(int(r["bytes"]) for r in und))

vd_by_rel = {r["rel"]: r for r in vd}
print("verdict rows", len(vd))
print("verdict rel == und rel set?", set(vd_by_rel) == set(r["rel"] for r in und))
print("in und not in vd", len(set(r["rel"] for r in und) - set(vd_by_rel)))
print("in vd not in und", len(set(vd_by_rel) - set(r["rel"] for r in und)))

cnt = collections.Counter(r["verdict"] for r in vd)
print("verdict counts", dict(cnt))

# 266 = 无法判定
tie = [r for r in vd if r["verdict"] == "无法判定"]
print("TIE count", len(tie))

cm_by_rel = {r["rel"]: r for r in cm}
ud_by_rel = {r["rel"]: r for r in ud}

# O/P distribution of tie
op = collections.Counter((int(r["O"]), int(r["P"])) for r in tie)
print("TIE O/P distribution (top20):", op.most_common(20))

# bnform distribution of tie
bn = collections.Counter(ud_by_rel[r["rel"]]["bnform"] for r in tie)
print("TIE bnform:", dict(bn))

# varatio distribution of tie (from content metrics)
vr_buckets = collections.Counter()
for r in tie:
    x = cm_by_rel[r["rel"]]
    var = float(x["varatio"])
    if var == 0: vr_buckets["0"] += 1
    elif var < 0.02: vr_buckets["(0,2%)"] += 1
    elif var < 0.10: vr_buckets["[2%,10%)"] += 1
    elif var < 0.30: vr_buckets["[10%,30%)"] += 1
    else: vr_buckets[">=30%"] += 1
print("TIE varatio buckets:", dict(vr_buckets))

# raw lines availability
print("cm rows", len(cm), "ud rows", len(ud))

# bytes of tie
tie_bytes = sum(int(ud_by_rel[r["rel"]]["bytes"]) for r in tie)
print("TIE bytes", tie_bytes)

# cross: bnform x (O>0?) x (P>0?)
cross = collections.Counter()
for r in tie:
    x = cm_by_rel[r["rel"]]
    b = ud_by_rel[r["rel"]]["bnform"]
    o0 = int(r["O"]) > 0
    p0 = int(r["P"]) > 0
    cross[(b, o0, p0)] += 1
for k in sorted(cross, key=lambda k: (k[0], k[1], k[2])):
    print("CROSS", k, cross[k])
