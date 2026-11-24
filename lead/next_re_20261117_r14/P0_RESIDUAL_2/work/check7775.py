#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check 0x7775C0 channel miss + are FPU functions called?"""
import sys,os,struct
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from res2_common import *
pe=PE();sw=Sweep(pe);at=Atlas();cov=load_set(COVERAGE)
def cF(a):
    b3=pe.try_read(a,3);b=pe.try_read(a,8)
    return a%16==0 and b3 and b3[0] not in E8E9EB and sw.endmap.get(a) in TERM and (form_c4a(b) or leafpat(b3))
ptr=set()
for sn in (".rdata",".data",".detour"):
    if sn not in pe.secs: continue
    s=pe.secs[sn];buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4;ws=struct.unpack_from("<%dI"%n,buf,0)
    for w in ws:
        if pe.tlo<=w<pe.thi: ptr.add(w)
# 7775C0
a=0x7775C0
print("0x7775C0 in_cov=%s cF=%s dataptr=%s first=%s pred=%s"%(
    a in cov,cF(a),a in ptr,hex(pe.byte(a)),sw.endmap.get(a)))
# scan .text for direct call/jmp rel32 to FPU targets
fpu_targets={0x403CE0,0x403D10,0x403D30,0x403D50,0x403D70,0x403D90,0x406920}
hits={t:[] for t in fpu_targets}
t=pe.secs[".text"];buf=pe.data[t["raw"]:t["raw"]+t["rawsize"]]
for i in range(0,len(buf)-5):
    if buf[i] in (0xE8,0xE9):
        rel=struct.unpack_from("<i",buf,i+1)[0]
        tgt=t["va"]+i+5+rel
        if tgt in hits: hits[tgt].append(hex(t["va"]+i))
for t0,v in hits.items(): print("%08X direct-call/jmp sites=%d %s"%(t0,len(v),v[:5]))
