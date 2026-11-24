#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify FPU addr coverage/atlas status + homogeneous baseline + channel recall split."""
import sys, os, struct, collections, random
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *
pe=PE();sw=Sweep(pe);at=Atlas()
cov=load_set(COVERAGE)
for a in (0x403CE0,0x403D10,0x403D30,0x406920,0x40A210):
    print("%08X in_atlas=%s in_cov=%s owner=%s"%(a,at.in_atlas(a),a in cov,at.owner(a)))
# count FPU-first in pool that are in cov (sanity)
fpu_in_cov=0; fpu_tot=0
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    if pe.byte(va) in (0xDD,0xDB):
        fpu_tot+=1
        if va in cov: fpu_in_cov+=1
print("FPU-first aligned+TERM+notatlas total=%d in_cov=%d notin=%d"%(fpu_tot,fpu_in_cov,fpu_tot-fpu_in_cov))

# homogeneous baseline: atlas interior positions that ALSO have pred in TERM
random.seed(20261117)
interior=[va for e,sz in at.rows for va in range((e+16+15)//16*16,e+sz,16) if va<pe.thi]
homog=[a for a in interior if sw.endmap.get(a) in TERM]
samp=random.sample(homog,min(5000,len(homog)))
def form(a): 
    b=pe.try_read(a,8);return form_c4a(b) or leafpat(pe.try_read(a,3))
print("homogeneous baseline (atlas interior & pred TERM): n_total=%d n_sample=%d form_pass=%d (%.2f%%)"%(
    len(homog),len(samp),sum(1 for a in samp if form(a)),100.0*sum(1 for a in samp if form(a))/len(samp)))

# channel recall: F vs G(data-ptr only) vs H(SEH/detour/jmp_abs), no old call/jmp sweep
ptr=set()
for sn in (".rdata",".data",".detour"):
    if sn not in pe.secs: continue
    s=pe.secs[sn]; buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4; ws=struct.unpack_from("<%dI"%n,buf,0)
    for w in ws:
        if pe.tlo<=w<pe.thi: ptr.add(w)
gate=load_set(GATE,0,True,lambda p:p[8]=="FUNC"); resid=load_set(RESID,0,True,lambda p:p[2]=="FUNC")
def cF(a):
    b3=pe.try_read(a,3);b=pe.try_read(a,8)
    return a%16==0 and b3 and b3[0] not in E8E9EB and sw.endmap.get(a) in TERM and (form_c4a(b) or leafpat(b3))
for nm,S in (("gate",gate),("resid",resid)):
    f=sum(1 for a in S if cF(a));g=sum(1 for a in S if a in ptr);u=sum(1 for a in S if cF(a) or a in ptr)
    print("%s: F=%d(%.1f%%) Gdata=%d(%.1f%%) F|G=%d(%.1f%%) /%d"%(nm,f,100*f/len(S),g,100*g/len(S),u,100*u/len(S),len(S)))
