# -*- coding: utf-8 -*-
"""_ocv_arith.py - verify the report's internal arithmetic and #6/#13 archive texts.
Read-only."""
import json, os, glob

D = "D:/Project/ra2-campaign-forge/.zcode/workflow-runs/"
W = "D:/Project/ra2-campaign-forge/lead/orch_claims_20261109/"
st = json.load(open(W+"_oc_stats_out.json", encoding="utf-8"))
C = [
 (1,"wrong_numeric","数少",True,True,"yes"),(2,"wrong_numeric","数少",True,True,"yes"),
 (3,"wrong_convention","口径混淆",True,True,"yes"),(4,"wrong_numeric","数多",True,True,"yes"),
 (5,"wrong_convention","口径混淆",True,True,"yes"),(6,"wrong_object","把设计实验当实跑",True,True,"hedged"),
 (7,"wrong_object","串对象",True,True,"hedged"),(8,"wrong_numeric","数多",True,True,"yes"),
 (9,"imprecise","口径混淆",True,True,"yes"),(10,"wrong_object","串对象",True,True,"hedged"),
 (11,"wrong_object","串对象",True,True,"no"),(12,"wrong_numeric","数少",True,True,"yes"),
 (13,"wrong_object","口径混淆",True,True,"yes"),(14,"wrong_numeric","数多",True,True,"hedged"),
 (15,"wrong_convention","口径混淆",True,True,"no"),(16,"wrong_object","串对象",True,True,"hedged"),
 (17,"wrong_object","口径混淆",True,True,"no"),(18,"wrong_convention","口径混淆",True,True,"hedged"),
 (19,"wrong_numeric","代数错",False,False,"self_recount"),(20,"wrong_numeric","代数错",False,False,"self_recount"),
]
from collections import Counter
print("=== A. independent recomputation of distributions ===")
print("verdict:", dict(Counter(x[1] for x in C)))
print("primary:", dict(Counter(x[2] for x in C)))
print("caught:", sum(x[3] for x in C), "misdirected:", sum(x[4] for x in C))
print("literal:", dict(Counter(x[5] for x in C)))
print("agree_with_stats_json:",
      dict(Counter(x[1] for x in C)) == st["verdict_distribution"],
      dict(Counter(x[2] for x in C)) == st["primary_nature_distribution"],
      sum(x[3] for x in C) == st["caught_by_subtask"],
      sum(x[4] for x in C) == st["misdirected_downstream"])
print("non-exclusive counts (from _oc_stats.py C[3] lists):", st["all_natures_distribution_non_exclusive"])
print("sum primary:", sum(st["primary_nature_distribution"].values()))

def lowered(p):
    src = open(p, encoding="utf-8").read()
    i = src.find("export const payload = ")
    if i < 0: return ""
    pl,_ = json.JSONDecoder().raw_decode(src[i+len("export const payload = "):])
    return pl.get("lowered","")

# #6 archived phrasing
print("=== B. #6 GP-A1 / PASS→CATCH in archives ===")
for p in sorted(glob.glob(D+"*.mjs")):
    if "89df48db" in p: continue
    for n,L in enumerate(lowered(p).splitlines(),1):
        if ("GP-A1" in L and ("CATCH" in L or "PASS" in L)) or "PASS→CATCH" in L:
            print(os.path.basename(p)[:24], f"lowered:{n}:", L.strip()[:300])

# #13 task book
print("=== C. #13 '4 件' / '最小硬项' in archives ===")
for p in sorted(glob.glob(D+"*.mjs")):
    if "89df48db" in p: continue
    for n,L in enumerate(lowered(p).splitlines(),1):
        if ("4 件最小" in L or "最小硬项" in L or ("4 件" in L and "最小" in L)):
            print(os.path.basename(p)[:24], f"lowered:{n}:", L.strip()[:300])

# #16 archive census prompt
print("=== D. #16 census regex in dwfrun-88c601f0 ===")
for n,L in enumerate(lowered(D+"dwfrun-88c601f0-dc93-4e6e-b752-86462aea6dc5.mjs").splitlines(),1):
    if "PAT_ANY" in L or "any(" in L and ("for" in L or "第一步" in L):
        print(f"lowered:{n}:", L.strip()[:300])

# #7 archive hedging
print("=== E. #7 c07_slot hedging in dwfrun-868215ce ===")
for n,L in enumerate(lowered(D+"dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs").splitlines(),1):
    if "c07_slot" in L and ("可能" in L or "真断言" in L or "重点" in L):
        print(f"lowered:{n}:", L.strip()[:320])
