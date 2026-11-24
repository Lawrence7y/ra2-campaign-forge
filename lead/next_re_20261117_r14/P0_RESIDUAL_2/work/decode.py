#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test (1) broadened getter pattern recall on gate; (2) clean-decode discriminator."""
import sys, os, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *

pe=PE(); sw=Sweep(pe); at=Atlas()
cov=load_set(COVERAGE)
gate=load_set(GATE,0,True,lambda p:p[8]=="FUNC")
resid=load_set(RESID,0,True,lambda p:p[2]=="FUNC")

def leaf_broad(b):
    if not b or len(b)<4: return False
    if leafpat(b): return True
    if b[0]==0x8B and (b[1]&0xF0)==0x50 and b[2]==0x24: return True
    return False

def form_broad(a):
    b=pe.try_read(a,8)
    return form_c4a(b) or leaf_broad(b)

for name,S in (("gate476",gate),("resid1096",resid)):
    f1=sum(1 for a in S if form_c4a(pe.try_read(a,8)) or leafpat(pe.try_read(a,3)))
    f2=sum(1 for a in S if form_broad(a))
    print("%-10s form=%d (%.1f%%) form_broad=%d (%.1f%%) /%d"%(
        name,f1,100.0*f1/len(S),f2,100.0*f2/len(S),len(S)))

def clean(T, span=48, window=32):
    d=pe.try_read(T,span)
    if not d: return 0,0
    nb=0; good=0
    for ins in md32(True).disasm(d,T):
        if ins.address-T>=window: break
        if ins.id==0: nb+=ins.size
        else: good+=ins.size
    return good, nb

for name,S in (("gate476",list(gate)),("resid1096",list(resid))):
    tot_g=tot_b=0; n_fullclean=0
    for a in S:
        g,b=clean(a); tot_g+=g; tot_b+=b
        if b==0: n_fullclean+=1
    print("%-10s fullclean=%d/%d (%.1f%%) total_good=%d total_byte=%d"%(
        name,n_fullclean,len(S),100.0*n_fullclean/len(S),tot_g,tot_b))

pool=[]
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
gapc=[a for a in pool if a not in cov]
print("pool\\cov n=%d form_broad=%d"%(len(gapc),sum(1 for a in gapc if form_broad(a))))
cls=collections.Counter(); fullclean=collections.Counter()
for a in gapc:
    b=pe.try_read(a,4); f=b[0] if b else -1
    g,bb=clean(a)
    k=('form' if form_broad(a) else ('mov' if f==0x8B else ('fpu' if f in (0xDD,0xDB) else 'other')))
    cls[k]+=1
    if bb==0: fullclean[k]+=1
for k in cls:
    print("  pool\\cov %-6s n=%d fullclean=%d (%.1f%%)"%(k,cls[k],fullclean[k],100.0*fullclean[k]/cls[k]))
