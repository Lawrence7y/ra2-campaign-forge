# -*- coding: utf-8 -*-
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
for r in D:
    sites=[]
    for s in r["chA_sites"]:
        ca=R.hx(s["call_addr"]); c=R.hx(s["callee"]) if s.get("callee") else "None"
        sites.append("%s->%s/%s/%s"%(ca,c,s["test_kind"],s["jcc_mnemonic"]))
    print(r["entry"], "p3=%d"%r["chA"]["p3"], "chB=%d"%len(r["chB"]),
          "sites:", " | ".join(sites) if sites else "NONE")
