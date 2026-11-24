#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01-V1 汇总分析：帧率 3 窗 + EIP 分桶 top-10 + 栈调用点。"""
import json, os
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01-V1"
E = os.path.join(BASE,"EVIDENCE")

rows=[json.loads(l) for l in open(os.path.join(E,"live45.ndjson"),encoding="utf-8") if l.strip()]
print("=== 帧率：3 个 >=10s 窗口 ===")
print("total samples=%d span=%.3fs frame %s -> %s" %
      (len(rows), rows[-1]["t"], rows[0]["frame"], rows[-1]["frame"]))

def window(t0,t1):
    a=min(rows,key=lambda r:abs(r["t"]-t0)); b=min(rows,key=lambda r:abs(r["t"]-t1))
    dt=b["t"]-a["t"]; df=b["frame"]-a["frame"]
    return a,b,dt,df,(df/dt if dt>0 else 0)

wins=[(0.0,12.0),(16.0,28.0),(32.0,44.0)]
rates=[]
for i,(t0,t1) in enumerate(wins,1):
    a,b,dt,df,fps=window(t0,t1); rates.append(fps)
    print("W%d: t=[%.3f,%.3f] dt=%.3fs frame=[%s,%s] df=%d fps=%.4f"
          %(i,a["t"],b["t"],dt,a["frame"],b["frame"],df,fps))
print("mean fps=%.4f  min=%.4f max=%.4f" % (sum(rates)/len(rates), min(rates), max(rates)))

# 整段
a,b,dt,df,fps=window(rows[0]["t"],rows[-1]["t"])
print("WHOLE: dt=%.3f df=%d fps=%.4f  (1000/fps=%.3f ms/frame)"%(dt,df,fps,1000/fps))
# 每帧墙钟 ms（逐窗）
for i,(t0,t1) in enumerate(wins,1):
    a,b,dt,df,fps=window(t0,t1)
    print("W%d ms/frame=%.3f"%(i,1000/fps))

print("\n=== EIP 分桶 top-10（全样本） ===")
raw=[]
for l in open(os.path.join(E,"eip_raw_hist.tsv"),encoding="utf-8"):
    if l.startswith("#") or not l.strip(): continue
    p=l.strip().split("\t"); raw.append((p[0],int(p[1]),float(p[2]),float(p[3])))
print("distinct EIP buckets=%d  total EIP samples=%d"%(len(raw),sum(x[1] for x in raw)))
for e,c,pt,px in raw[:10]:
    print("  %s  hits=%d  pct_total=%.4f%%  pct_text=%.4f%%"%(e,c,pt,px))

print("\n=== 栈调用点（dense 15s） ===")
sites={}
for l in open(os.path.join(E,"stack_dense.ndjson"),encoding="utf-8"):
    if not l.strip(): continue
    r=json.loads(l); sites[r["site"]]=sites.get(r["site"],0)+1
for s,c in sorted(sites.items(),key=lambda x:-x[1]):
    print("  %s  hits=%d"%(s,c))
