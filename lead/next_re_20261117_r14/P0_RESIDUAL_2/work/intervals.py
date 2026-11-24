#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build function intervals (atlas sizes + coverage body lengths), then test:
- are known positives inside another function body? (should be ~0)
- are pool\cov candidates inside a body (label) or in gap (possible entry)?
Also measure four-criteria recall on unbiased positives (gate 476) vs biased (resid).
"""
import sys, os, re, collections, bisect
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *

pe=PE(); sw=Sweep(pe); at=Atlas()
cov=load_set(COVERAGE)
gate=load_set(GATE,0,True,lambda p:p[8]=="FUNC")
resid=load_set(RESID,0,True,lambda p:p[2]=="FUNC")

# ---- build intervals ----
intervals=[]  # (start,end) exclusive
for e,sz in at.rows:
    if sz>0: intervals.append((e,e+sz))
# parse body lengths from gate & resid evidence
def parse_len(ev):
    m=re.search(r'body_len=(\d+)',ev)
    if m: return int(m.group(1))
    m=re.search(r'body=(\d+)\(',ev)
    if m: return int(m.group(1))
    return None
n_covbody=0
import csv
for path,colsrc,colvl in ((GATE,11,None),(RESID,4,None)):
    with open(path,encoding="utf-8",errors="replace") as f:
        rdr=csv.reader(f,delimiter="\t"); next(rdr)
        for p in rdr:
            if len(p)<=colsrc: continue
            a=int(p[0],16)
            ln=parse_len(p[colsrc])
            if ln and ln>0:
                intervals.append((a,a+ln)); n_covbody+=1
# merge intervals
intervals.sort()
merged=[]
for a,b in intervals:
    if merged and a<=merged[-1][1]: merged[-1][1]=max(merged[-1][1],b)
    else: merged.append([a,b])
starts=[a for a,_ in merged]
print("intervals: atlas=%d + covbody=%d -> merged=%d"%(len(at.rows),n_covbody,len(merged)))

def inside_body(a):
    i=bisect.bisect_right(starts,a)-1
    if i>=0 and merged[i][0]<a<merged[i][1]:  # strictly inside (not at entry)
        return merged[i]
    return None

# pool
pool=[]
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
poolset=set(pool)
newc=sorted(poolset-cov)

for name,S in (("gate476",gate),("resid1096",resid),("pool\\cov",set(newc))):
    ins=sum(1 for a in S if inside_body(a))
    print("%-12s n=%d inside another function body=%d (%.1f%%)"%(name,len(S),ins,100.0*ins/len(S)))

# four-criteria recall components on gate vs resid (unbiased vs biased)
def comps(a):
    b=pe.try_read(a,8); b3=pe.try_read(a,3)
    return dict(fb=(b3[0] not in E8E9EB) if b3 else False,
                pt=sw.endmap.get(a) in TERM,
                form=form_c4a(b) or leafpat(b3))
for name,S in (("gate476",gate),("resid1096",resid)):
    c=collections.Counter()
    for a in S:
        x=comps(a)
        for k,v in x.items(): c[k]+=v
        c['all4']+= (x['fb'] and x['pt'] and x['form'] and a%16==0)
    print("%-12s fb=%d pt=%d form=%d all4=%d /%d"%(name,c['fb'],c['pt'],c['form'],c['all4'],len(S)))

# how many pool\cov are NOT inside a body = gap candidates
gapc=[a for a in newc if not inside_body(a)]
print("pool\\cov total=%d ; inside body=%d ; gap(not in body)=%d"%(len(newc),len(newc)-len(gapc),len(gapc)))
# gap candidates that pass form
gf=[a for a in gapc if (form_c4a(pe.try_read(a,8)) or leafpat(pe.try_read(a,3)))]
print("  gap candidates passing form = %d"%len(gf))
with open(os.path.join(os.path.dirname(HERE),"EVIDENCE","gap_candidates.tsv"),"w",encoding="utf-8") as f:
    f.write("addr\tin_body\tform\tfirst_byte\tpred\n")
    for a in newc:
        x=comps(a)
        f.write("%08X\t%d\t%d\t%s\t%s\n"%(a,1 if inside_body(a) else 0,x['form'],
                pe.byte(a) if pe.byte(a) is not None else -1, sw.endmap.get(a) or "?"))
