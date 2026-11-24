# -*- coding: utf-8 -*-
# _cv_na_20261108.py — 独立扫描候选/母本全文 n/a（甲 confidence 值域残留）并比对唯一命中（只读）
import re

BASE = "D:/Project/ra2-campaign-forge/"
MASTER = BASE + "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CAND   = BASE + "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"

pat = re.compile(r"[nN]/[aA]")  # 严格无空格口径，与审阅员一致；宽口径结果已另行登记
res = {}
for name, path in (("master", MASTER), ("cand", CAND)):
    t = open(path, "rb").read().decode("utf-8")
    hits = [(i + 1, L.strip()) for i, L in enumerate(t.split("\n")) if pat.search(L)]
    res[name] = hits
    print("%s: n/a-like hits = %d" % (name, len(hits)))
    for ln, txt in hits:
        print("   :%d| %s" % (ln, txt[:160]))

print("== 唯一命中同位逐字比对 ==")
if len(res["cand"]) == 1 and len(res["master"]) == 1:
    same = res["cand"][0][1] == res["master"][0][1]
    print("cand:%d text == master:%d text ->" % (res["cand"][0][0], res["master"][0][0]), same)
    if not same:
        print("  cand:", res["cand"][0][1][:160])
        print("  mast:", res["master"][0][1][:160])
else:
    print("命中数非 1：cand=%d master=%d（需逐条人工比对，上表已列出）")

print("== FRESHNESS 置信域文本核对（候选 :227 一带） ==")
cl = open(CAND, "rb").read().decode("utf-8").split("\n")
for i in range(219, 230):
    print("   %d| %s" % (i, cl[i-1][:150]))
