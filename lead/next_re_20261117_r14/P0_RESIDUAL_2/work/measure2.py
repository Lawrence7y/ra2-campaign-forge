#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure body-structure signals: padding-before, ret-termination, calls-to-known."""
import sys, os, collections, random, struct
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from res2_common import *

pe = PE(); sw = Sweep(pe); at = Atlas()
cov = load_set(COVERAGE)
gate = load_set(GATE, 0, True, lambda p: p[8]=="FUNC")
resid = load_set(RESID, 0, True, lambda p: p[2]=="FUNC")
known = cov | gate | resid
pool = []
for va in range((pe.tlo+15)//16*16, pe.thi, 16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins = sw.insn_at(pe, va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
poolset=set(pool)
pos = sorted((gate|resid)&poolset)
newc = sorted(poolset - cov)

def pad_run(T, mx=16):
    n=0; f=None
    for off in range(1,mx+1):
        b=pe.byte(T-off)
        if b is None: break
        if b in (0x90,0xCC):
            if f is None: f=b
            elif b!=f: break
            n+=1
        else: break
    return n,f

def body(T, maxb=0x400):
    d=pe.try_read(T,maxb)
    if not d: return dict(end=None,ln=0,ncall=0,ninsn=0,retpos=None)
    end=None; ln=0; ncall=0; ninsn=0; retpos=None
    for ins in md32(True).disasm(d,T):
        ninsn+=1
        if ins.id:
            if ins.mnemonic in ("ret","retn","retf"):
                end="ret"; ln=ins.address+ins.size-T; retpos=ln; break
            if ins.mnemonic=="jmp":
                end="jmp"; ln=ins.address+ins.size-T; break
            if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
                try:
                    tgt=int(ins.op_str,16)
                    if tgt in known or at.in_atlas(tgt): ncall+=1
                except: pass
        ln=ins.address+ins.size-T
        if ln>=maxb: break
    return dict(end=end,ln=ln,ncall=ncall,ninsn=ninsn,retpos=retpos)

def profile(a):
    p,f=pad_run(a)
    bd=body(a)
    return dict(pad=p,padfill=f,end=bd['end'],ln=bd['ln'],ncall=bd['ncall'],
                b0=pe.byte(a))

def summarize(name, arr, lim=None):
    arr2 = arr if lim is None else arr[:lim]
    c=collections.Counter(); ends=collections.Counter(); nc=collections.Counter()
    for a in arr2:
        p=profile(a)
        c['pad>=1']+=p['pad']>=1; c['pad>=2']+=p['pad']>=2
        c['pad>=4']+=p['pad']>=4; c['pad>=8']+=p['pad']>=8
        c['pad_0x90']+=(p['padfill']==0x90); c['pad_0xCC']+=(p['padfill']==0xCC)
        ends[p['end']]+=1
        c['end_ret_or_jmp']+=p['end'] in ('ret','jmp')
        c['end_ret']+=p['end']=='ret'
        c['ncall>=1']+=p['ncall']>=1
        c['ret_and_pad2']+=(p['end'] in ('ret','jmp') and p['pad']>=2)
        c['ret_pad2_call']+=(p['end']=='ret' and p['pad']>=2 and p['ncall']>=1)
        nc[p['ncall']]+=1
    n=len(arr2)
    print("\n=== %s n=%d ===" % (name,n))
    for k in ['pad>=1','pad>=2','pad>=4','pad>=8','pad_0x90','pad_0xCC',
              'end_ret_or_jmp','end_ret','ncall>=1','ret_and_pad2','ret_pad2_call']:
        print("  %-16s %5d/%d = %.1f%%" % (k,c[k],n,100.0*c[k]/n if n else 0))
    print("  ends:",dict(ends))
    print("  ncall dist:",dict(sorted(nc.items())[:8]))

random.seed(20261117)
base16=random.sample(range((pe.tlo+15)//16*16,pe.thi,16),5000)
summarize("POSITIVES(pool)",pos)
summarize("NEW pool\\cov",newc)
summarize("BASELINE random16",base16)
