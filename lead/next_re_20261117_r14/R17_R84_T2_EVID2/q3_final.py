#!/usr/bin/env python3
# Q3 定稿：规则=目录内“已裁件”>=3 且同向占比>=75% => 该目录平票件随多数派
import csv, os
from collections import defaultdict, Counter
R=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def load(p): return list(csv.DictReader(open(p,encoding="utf-8",newline=""),delimiter="\t"))
vd=load(os.path.join(R,"R17_R81_T2_EVID","_verdicts.tsv"))
ud={r["rel"]:int(r["bytes"]) for r in load(os.path.join(R,"R17_R81_T2_EVID","_undead_evid.tsv"))}
def parent(rel):
    p=os.path.dirname(rel); return p if p else "(root)"
dec=defaultdict(Counter)
for r in vd:
    if r["verdict"] in ("对象抄本","过程输出"):
        dec[parent(r["rel"])][r["verdict"]]+=1
tie=[r for r in vd if r["verdict"]=="无法判定"]

def decide_dir(d, minn=3, q=0.75):
    c=dec[d]; n=c["对象抄本"]+c["过程输出"]
    if n<minn: return None
    o,p=c["对象抄本"],c["过程输出"]
    maj=max(o,p); lab="对象抄本" if o>p else ("过程输出" if p>o else None)
    if lab is None or maj/n<q: return None
    return lab,n,maj/n

res=[]; unres=[]
for r in tie:
    dd=decide_dir(parent(r["rel"]))
    if dd: res.append((r,dd))
    else: unres.append(r)
print("COVER", len(res),"/",len(tie), "bytes", sum(ud[r["rel"]] for r,_ in res))
print("UNRES", len(unres),"bytes",sum(ud[r["rel"]] for r in unres))

def decide_dir_unanim(d,minn=3):
    c=dec[d]; n=c["对象抄本"]+c["过程输出"]
    if n<minn: return None
    o,p=c["对象抄本"],c["过程输出"]
    if o==0 or p==0: return "对象抄本" if o>p else "过程输出"
    return None
res2=[r for r in tie if decide_dir_unanim(parent(r["rel"]))]
print("COVER unanim",len(res2),"bytes",sum(ud[r["rel"]] for r in res2))

ok=n=0
for d,c in dec.items():
    labs=["对象抄本"]*c["对象抄本"]+["过程输出"]*c["过程输出"]
    if not decide_dir(d): continue
    for i,lab in enumerate(labs):
        others=labs[:i]+labs[i+1:]
        if not others: continue
        cc=Counter(others); o=cc["对象抄本"]; p=cc["过程输出"]
        if o==p: continue
        pred="对象抄本" if o>p else "过程输出"
        n+=1; ok+=(pred==lab)
print("LOO-rule-triggered", ok,"/",n, round(ok/n,4) if n else "NA")

with open(os.path.join(R,"R17_R84_T2_EVID2","q3_final.txt"),"w",encoding="utf-8") as f:
    f.write("规则: 同 EVIDENCE 目录内已裁件>=3 且同向>=75% => 该目录平票件随多数派(分母=已裁件)\n")
    f.write(f"覆盖率: {len(res)}/{len(tie)} 件 / {sum(ud[r['rel']] for r,_ in res)} B ; 仍单列 {len(unres)} 件\n")
    f.write(f"严格一致(100%同向)口径: {len(res2)} 件 / {sum(ud[r['rel']] for r in res2)} B\n")
    f.write(f"留一法(仅触发规则的目录): {ok}/{n} = {ok/n:.4f}\n")
