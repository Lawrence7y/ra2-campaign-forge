#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽样 c4b leaf-shape 候选，看它们是否像函数入口还是函数中部标签。"""
import os, sys, struct, random
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
from resid_common import (RawPE,Sweep,Atlas,md_new,COVERAGE,PROBE,OUTSIDE,
                          disasm_at,predecessor,JCC,TERM_KINDS)
ITEMS=[(0xA8EC7C,0xA8EC80),(0xA8ECBC,0xA8ECC0),(0xB0F4EC,0xB0F4F0)]
TERM_MN={"ret","retn","retf","jmp"}

def load(p,col=0):
    s=set()
    with open(p,encoding="utf-8",errors="replace") as f:
        f.readline()
        for ln in f:
            if not ln.strip():continue
            t=ln.rstrip("\n").split("\t")
            try:s.add(int(t[col],16))
            except:pass
    return s

def leaf_pattern(b):
    if len(b)<3:return False
    if b[0]==0x8B and (b[1]&0xF0)==0x40 and b[2]==0x24:return True
    if b[0]==0x8B and b[1]==0x41:return True
    if b[0] in (0x57,0x56,0x53):return True
    return False

def body_term(pe,T,limit=4096):
    for i in md_new().disasm(pe.read(T,min(limit,65536)),T):
        if i.mnemonic in TERM_MN:
            return True,(i.address+i.size-T),i.mnemonic
    return False,None,None

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe=RawPE();t=pe.byname[".text"];TLO=pe.imagebase+t["va"];THI=TLO+t["vsize"]
    sw=Sweep(pe,TLO,THI);at=Atlas()
    cov=load(COVERAGE);probe=load(PROBE);outside=load(OUTSIDE)
    c4b=[]
    for A in range((TLO+15)&~15,THI,16):
        if at.in_atlas(A):continue
        pr=predecessor(pe,sw,A)
        if pr["kind"] not in TERM_KINDS:continue
        raw3=pe.read(A,3)
        if not raw3:continue
        first=disasm_at(pe,A,n=3,span=24)
        fmn=first[0][0] if first else ".byte"
        if fmn in JCC or fmn==".byte":continue
        okl=leaf_pattern(raw3)
        bt,bl,term=body_term(pe,A)
        if okl and bt and bl and bl>=2:
            resid=A not in cov and A not in probe and A not in outside
            c4b.append((A,resid,bl,term,pr["kind"],first[:3]))
    resid=[x for x in c4b if x[1]]
    print("c4b total",len(c4b),"resid",len(resid))
    random.seed(20261117)
    sample=random.sample(resid,18)
    for A,resid,bl,term,pk,first in sorted(sample):
        ins=" | ".join("%s %s"%i[:2] for i in first)
        print("%08X body=%-4s term=%-4s prev=%-5s  %s"%(A,bl,term,pk,ins))

if __name__=="__main__":main()
