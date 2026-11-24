#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Examine gate476 form-FAILURES: what prologues do the missed true entries have?"""
import sys, os, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *

pe=PE(); sw=Sweep(pe); at=Atlas()
cov=load_set(COVERAGE)
gate=load_set(GATE,0,True,lambda p:p[8]=="FUNC")
resid=load_set(RESID,0,True,lambda p:p[2]=="FUNC")

def fb_of(a):
    b=pe.try_read(a,4)
    return b[0] if b else -1

gf=[a for a in sorted(gate) if not (form_c4a(pe.try_read(a,8)) or leafpat(pe.try_read(a,3)))]
print("gate form-FAIL = %d / %d"%(len(gf),len(gate)))
fb=collections.Counter(fb_of(a) for a in gf)
print("gate form-FAIL first-byte histogram:")
for k,v in fb.most_common(25): print("  %02X : %d"%(k,v))
print("\ngate form-FAIL first instructions (sample 30):")
for a in gf[:30]:
    ins=sw.insn_at(pe,a,span=16) if False else None
    d=pe.try_read(a,12)
    ii=next(md32(True).disasm(d,a),None)
    s=(ii.mnemonic+' '+ii.op_str) if ii else '?'
    print("  %08X fb=%02X  %s"%(a,fb_of(a),s))

def prologue_class(a):
    b=pe.try_read(a,8); b3=pe.try_read(a,3)
    if not b3: return 'none'
    if form_c4a(b) or leafpat(b3): return 'form'
    f=b[0]
    if 0x50<=f<=0x57: return 'push_reg'
    if f in (0x6A,0x68): return 'push_imm'
    if f in (0x83,0x81) and len(b)>1 and b[1]==0xEC: return 'subesp'
    if f==0x55: return 'push_ebp'
    if f in (0x8B,0x8D,0x89,0x33,0x31,0xA1,0xA0,0xC6,0xB8,0xB9): return 'mov_leaf'
    if f==0x51: return 'push_ecx'
    return 'other_%02X'%f

cg=collections.Counter(prologue_class(a) for a in gate)
print("\ngate476 prologue classes:")
for k,v in cg.most_common(): print("  %-12s %d"%(k,v))

pool=[]
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
gapc=[a for a in pool if a not in cov]
cn=collections.Counter(prologue_class(a) for a in gapc)
print("\npool\\cov (%d) prologue classes:"%len(gapc))
for k,v in cn.most_common(): print("  %-12s %d"%(k,v))
