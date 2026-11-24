# -*- coding: utf-8 -*-
"""Detailed per-call-site evidence for selected candidates: caller VA, grade, name, and param bytes before call."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, IB, SECS, md32, va2off, read_va
from capstone.x86 import X86_OP_IMM

WORK=os.path.dirname(__file__)
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
atlas=[]
for line in open(ATLAS,encoding="utf-8",errors="replace"):
    f=line.split("\t")
    if f and f[0]!="entry":
        try: atlas.append((int(f[0],16),int(f[1])))
        except: pass
atlas.sort()
def caller_of(s):
    lo,hi,best=0,len(atlas)-1,None
    while lo<=hi:
        m=(lo+hi)//2
        if atlas[m][0]<=s: best=m;lo=m+1
        else: hi=m-1
    if best is not None and atlas[best][0]<=s<atlas[best][0]+atlas[best][1]: return atlas[best][0]
    return None
cov={}
for line in open(COV,encoding="utf-8",errors="replace"):
    f=line.rstrip("\n").split("\t")
    if len(f)>=5 and f[0]!="entry": cov[f[0].upper()]=(f[1],f[4],f[2])
text=[s for s in SECS if s[0]==".text"][0]
blob=DATA[text[4]:text[4]+text[3]]
md=md32()
# collect call instr with 8 preceding instrs for context
calls={}
prev=[]
for ins in md.disasm(blob,IB+text[1]):
    if ins.mnemonic=="call" and ins.bytes and ins.bytes[0]==0xE8 and ins.operands and ins.operands[0].type==X86_OP_IMM:
        tgt=ins.operands[0].imm&0xffffffff
        calls.setdefault(tgt,[]).append((ins.address, list(prev[-8:])))
    prev.append((ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))

targets=["00407780","00407F40","00407FB0","007C9442"]
for e in targets:
    va=int(e,16)
    print("\n=== %s %s ==="%(e,cov.get(e,("?","?","?"))[2]))
    for site,ctx in calls.get(va,[])[:12]:
        ce=caller_of(site)
        ci=cov.get("%08X"%ce,("?","?","?")) if ce else ("?","?","?")
        print("  site %08X caller %s grade %s name %s"%(site,("%08X"%ce) if ce else "?",ci[1],ci[2]))
        for a,h,m,o in ctx:
            print("      %08X %-18s %s %s"%(a,h,m,o))
