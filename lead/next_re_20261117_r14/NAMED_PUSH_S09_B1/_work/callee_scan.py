# -*- coding: utf-8 -*-
"""对所有 chA 站点 callee 做精确返回常量剖析，找多值状态码。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retprof
WORK=os.path.dirname(os.path.abspath(__file__))
ANA=json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
seen={}
for a in ANA:
    for s in a.get("chA",{}).get("sites",[]):
        c=s.get("callee")
        if c and c not in seen:
            seen[c]=(a["entry"],s["call_addr"])
for callee in sorted(seen):
    entry,call=seen[callee]
    rets=retprof.profile(callee)
    vals=sorted(set(str(v) for addr,v,bb in rets))
    print("%08X (row %s call@%08X) nrets=%d values=%s" % (callee,entry,call,len(rets),vals))
