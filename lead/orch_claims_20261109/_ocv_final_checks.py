# -*- coding: utf-8 -*-
"""_ocv_final_checks.py - targeted checks on disputed points. Read-only."""
import json, os, glob, re

D = "D:/Project/ra2-campaign-forge/.zcode/workflow-runs/"
W = "D:/Project/ra2-campaign-forge/lead/orch_claims_20261109/"

def lowered(p):
    src = open(p, encoding="utf-8").read()
    i = src.find("export const payload = ")
    if i < 0: return ""
    try:
        pl, _ = json.JSONDecoder().raw_decode(src[i+len("export const payload = "):])
        return pl.get("lowered", "")
    except Exception:
        return ""

# A) #11/#15/#17: does any OTHER archive contain the literal assertion?
keys = ["n4_yi_final 是门禁挑错中稿", "挑错中稿", "SELF_TEST=FAIL 是脚本缺陷",
        "H5 修好就能插生产门禁", "修好就能插", "修好 H5 之后，V12 能不能插",
        "三层共用同一套字面词表", "共用字面词表", "任何(... for ... in ...)",
        "any(... for ... in ...)", "弄错了", "更正"]
print("=== A. literal assertions across archives (excluding current 89df48db) ===")
for k in keys:
    hits = []
    for p in sorted(glob.glob(D+"*.mjs")):
        if "89df48db" in p: continue
        low = lowered(p)
        for n,L in enumerate(low.splitlines(),1):
            if k in L:
                hits.append((os.path.basename(p)[:20], n, L.strip()[:260]))
    print(f"KEY {k!r}: {len(hits)} hits")
    for h in hits[:6]: print("   ", h)

# B) #8: does dwfrun-5876dbf3 say 'four problems' literally, and what does the
#    subtask report say about the other 2?
p = D+"dwfrun-5876dbf3-36f9-4f9c-8ec3-8a7fefb07395.mjs"
low = lowered(p).splitlines()
print("=== B. #8 literal in dwfrun-5876dbf3 ===")
for n,L in enumerate(low,1):
    if "四条" in L or "逐条重判" in L:
        print(f"lowered:{n}: {L.strip()[:300]}")

# C) #17: CLAIMS 'still 4 defects' vs on-disk 6 / 8
for f, lo, hi in [("_h5_DESIGN.md",290,301),("H5_GOVERNANCE_FIX.md",466,479)]:
    p = "D:/Project/ra2-campaign-forge/lead/h5_governance_20261109/"+f
    L = open(p,encoding="utf-8").read().splitlines()
    rows = [x for x in L[lo-1:hi] if re.match(r"^\|\s*\d+\s*\|", x)]
    print(f"=== C. {f} numbered defect rows = {len(rows)} ===")
    for x in rows: print("   ", x[:160])

# D) report internal: '18 条全部被当场纠正' vs '3 条找不到字面原任务书'
rep = open(W+"_oc_ORCH_CLAIMS_AUDIT.md",encoding="utf-8").read().splitlines()
print("=== D. report §3(b)(c)(d) verbatim head ===")
for i in list(range(171,190)):
    print(f"{i}: {rep[i-1][:260]}")

# E) stats: misdirected_downstream=18 but not_caught=[19,20], literal=no=3
st = json.load(open(W+"_oc_stats_out.json", encoding="utf-8"))
print("=== E. _oc_stats_out.json key fields ===")
for k in ("caught_by_subtask","not_caught","not_caught_ids","misdirected_downstream","literal_in_taskbook","wrong","imprecise","correct"):
    print(k, "=", st[k])

# F) #9: archived self statement
print("=== F. #9 archived statements ===")
for p in sorted(glob.glob(D+"*.mjs")):
    low = lowered(p)
    for n,L in enumerate(low.splitlines(),1):
        if "共用同一套字面词表" in L or "共用字面词表" in L:
            print(os.path.basename(p)[:24], f"lowered:{n}:", L.strip()[:280])
