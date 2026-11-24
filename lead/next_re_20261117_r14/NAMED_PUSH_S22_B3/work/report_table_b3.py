# -*- coding: utf-8 -*-
"""Emit a compact per-row anchor table (markdown) for REPORT.md + PROGRESS.md text."""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.dirname(HERE)
V=json.load(open(os.path.join(HERE,"verdicts.json"),encoding="utf-8"))

def cls(name):
    import re
    m=re.search(r'TClassFactory_V(.+?)__',name)
    return m.group(1) if m else name

# anchor summary table
print("## ANCHOR TABLE")
print("| # | entry | 类 | ① | ② RTTI slot / vt | ② C1 主vt槽0 | ③ QI站点/被调/常量 | ④ alloc→ctor→reg→CLSID/host | 裁定 |")
print("|---:|---|---|---|---|---|---|---|---|")
for i,v in enumerate(V,1):
    r1,r2,c1,r3,r4=v["r1"],v["r2"],v["special_C1"],v["r3b"],v["r4"]
    r1s="PASS" if (r1["in_text"] and r1["n_skipdata"]==0) else "FAIL"
    r2s="%s/#%s"%(r2["slot_va"],r2["slotno"])
    c1s="%s%s"%("PASS" if c1["ok"] else "FAIL", "="+c1["mainvt_slot0_actual"])
    consts=",".join(x[6:] if x.startswith("000000") else x for x in r3["qi_consts"]) or "none"
    r3s="%s/%s/{%s}"%(r3["qi_site"]["addr"],r3["qi_va"],consts)
    r4s="host=%s clsid=%s dtor=%s"%(r4["host_func"], r4.get("clsid","-"), r4["anchor_in_dtor"])
    verd="**成立**" if v["all_four"] else "不成立"
    print("| %d | %s | %s | %s | %s | %s | %s | %s | %s |"%(
        i,v["entry"],cls(v["name"]),r1s,r2s,c1s,r3s,r4s,verd))
