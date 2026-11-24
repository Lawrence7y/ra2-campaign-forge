# -*- coding: utf-8 -*-
"""对所有 chA 站点 callee 做精确返回常量剖析，找多值状态码（>=3 distinct 或 -1/HRESULT），
避免 recore 只跟踪 mov/xor 造成的漏判。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import retprof
WORK=os.path.dirname(os.path.abspath(__file__))
ANA=json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
seen={}
for a in ANA:
    for s in a.get("chA",{}).get("sites",[]):
        c=s.get("callee")
        if c and c not in seen:
            seen[c]=(a["entry"],s["call_addr"])
for callee,(entry,call) in sorted(seen.items()):
    rets=retprof.profile(callee)
    vals=set()
    for addr,v,bb in rets:
        vals.add(str(v))
    print("%08X (row %s call@%08X) rets=%d values=%s" % (callee,entry,call,len(rets),sorted(vals)))
