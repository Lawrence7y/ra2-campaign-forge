#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze Channel G reference evidence as a discriminator.
Measure: on known positives, #data-referenced, pointer count, dense-run membership.
On pool\cov gap candidates, same signals. Check 0x7775C0 prologue class.
"""
import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *

pe=PE(); sw=Sweep(pe); at=Atlas()
cov=load_set(COVERAGE)
gate=load_set(GATE,0,True,lambda p:p[8]=="FUNC")
resid=load_set(RESID,0,True,lambda p:p[2]=="FUNC")

# data pointer map (dwords in rdata/data pointing to text)
ptrcnt=collections.Counter()
for sn in (".rdata",".data"):
    s=pe.secs[sn]; buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4; ws=struct.unpack_from("<%dI"%n,buf,0)
    for w in ws:
        if pe.tlo<=w<pe.thi: ptrcnt[w]+=1

# dense run targets
denseT=set()
def dense_runs(sname,minrun=3):
    s=pe.secs[sname]; buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4; ws=struct.unpack_from("<%dI"%n,buf,0)
    out=[]; i=0
    while i<n:
        if pe.tlo<=words_ok(ws[i]):
            j=i
            while j<n and pe.tlo<=ws[j]<pe.thi: j+=1
            if j-i>=minrun:
                out.append((s["va"]+4*i,j-i,list(ws[i:j])))
            i=j
        else: i+=1
    return out
def words_ok(w): return w<pe.thi
for sn in (".rdata",".data"):
    for va,n,ws in dense_runs(sn):
        for w in ws: denseT.add(w)

# call/jmp reference counts (byte channel) — NEW independent sweep using audit_lib
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, sweep_calls
bn=Bin()
calls,jmps,stats=sweep_calls(bn)
callcnt=collections.Counter()
for t,sites in calls.items(): callcnt[t]=len(sites)
jmpcnt=collections.Counter()
for t,sites in jmps.items(): jmpcnt[t]=len(sites)

def prof(a):
    b=pe.try_read(a,8); b3=pe.try_read(a,3)
    return dict(ptr=ptrcnt.get(a,0),dense=a in denseT,
                call=callcnt.get(a,0),jmp=jmpcnt.get(a,0),
                form=form_c4a(b) or leafpat(b3),
                fb=b3[0] if b3 else -1)

# pool & gap candidates
pool=[]
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
poolset=set(pool)
gapc=[a for a in poolset if a not in cov]

for name,S in (("gate476",gate),("resid1096",resid),("pool\\cov",set(gapc))):
    c=collections.Counter()
    for a in S:
        p=prof(a)
        c['ptr>=1']+=p['ptr']>=1; c['ptr>=2']+=p['ptr']>=2
        c['dense']+=p['dense']; c['call>=1']+=p['call']>=1
        c['jmp>=1']+=p['jmp']>=1; c['anyref']+=(p['ptr']>=1 or p['call']>=1 or p['jmp']>=1)
        c['form']+=p['form']
        c['anyref_form']+=((p['ptr']>=1 or p['call']>=1 or p['jmp']>=1) and p['form'])
        c['call_or_ptr']+=((p['call']>=1) or (p['ptr']>=1))
    n=len(S)
    print("\n%s n=%d"%(name,n))
    for k in ['ptr>=1','ptr>=2','dense','call>=1','jmp>=1','anyref','form','anyref_form','call_or_ptr']:
        print("  %-12s %5d/%d = %.1f%%"%(k,c[k],n,100.0*c[k]/n if n else 0))
