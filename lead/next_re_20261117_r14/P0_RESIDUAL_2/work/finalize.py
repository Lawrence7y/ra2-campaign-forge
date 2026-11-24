#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finalize ENUM universe + channel attribution + FUNC candidate verification."""
import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *

pe=PE(); sw=Sweep(pe); at=Atlas()
cov=load_set(COVERAGE)
# data ptr refs
ptr=collections.Counter(); ptrsrc={}
for sn in (".rdata",".data"):
    s=pe.secs[sn]; buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4; ws=struct.unpack_from("<%dI"%n,buf,0)
    for i,w in enumerate(ws):
        if pe.tlo<=w<pe.thi:
            ptr[w]+=1; ptrsrc.setdefault(w,[]).append("%s:%08X"%(sn,s["va"]+4*i))

pool=[]
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
gapc=[a for a in pool if a not in cov]
print("ENUM universe (pool\\cov) =",len(gapc))
print("  with data-ptr ref =",sum(1 for a in gapc if ptr.get(a,0)>0))

# FUNC candidates: pool\cov passing strict form, not in body
# reuse interval parse
import re,csv,bisect
intervals=[(e,e+sz) for e,sz in at.rows if sz>0]
def pl(ev):
    m=re.search(r'body_len=(\d+)',ev) or re.search(r'body=(\d+)\(',ev)
    return int(m.group(1)) if m else None
for path,col in ((GATE,11),(RESID,4)):
    with open(path,encoding="utf-8",errors="replace") as f:
        r=csv.reader(f,delimiter="\t"); next(r)
        for p in r:
            if len(p)>col:
                ln=pl(p[col])
                if ln and ln>0: intervals.append((int(p[0],16),int(p[0],16)+ln))
intervals.sort(); mg=[]
for a,b in intervals:
    if mg and a<=mg[-1][1]: mg[-1][1]=max(mg[-1][1],b)
    else: mg.append([a,b])
st=[a for a,_ in mg]
def inbody(a):
    i=bisect.bisect_right(st,a)-1
    return i>=0 and mg[i][0]<a<mg[i][1]

func=[]
for a in gapc:
    b3=pe.try_read(a,3); b=pe.try_read(a,8)
    f4=(a%16==0) and b3 and b3[0] not in E8E9EB and (sw.endmap.get(a) in TERM) and (form_c4a(b) or leafpat(b3))
    if f4 and not inbody(a): func.append(a)
print("FUNC (4crit + not-in-body) =",len(func))
print("\nFUNC candidates detail:")
for a in sorted(func):
    d=pe.try_read(a,16)
    ii=next(md32(True).disasm(d,a),None)
    s=(ii.mnemonic+' '+ii.op_str) if ii else '?'
    pred=sw.endmap.get(a)
    print("  %08X  fb=%02X pred=%-5s ptr=%d first=%s"%(
        a,d[0],pred or '?',ptr.get(a,0),s))
