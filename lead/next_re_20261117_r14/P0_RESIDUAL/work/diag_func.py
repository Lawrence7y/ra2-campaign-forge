#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断：1096 FUNC 的构成（c4a vs c4b）、c4b 基线鉴别力、通道 A 的 85 FUNC 来源。"""
import os, sys, struct, collections, random
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
from resid_common import (RawPE,Sweep,Atlas,md_new,COVERAGE,PROBE,OUTSIDE,
                          disasm_at,predecessor,JCC,TERM_KINDS)

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

def leaf(b):
    if len(b)<3:return False
    if b[0]==0x8B and (b[1]&0xF0)==0x40 and b[2]==0x24:return True
    if b[0]==0x8B and b[1]==0x41:return True
    if b[0] in (0x57,0x56,0x53):return True
    return False

TERM_MN={"ret","retn","retf","jmp"}
def body(pe,T,limit=4096):
    for i in md_new().disasm(pe.read(T,min(limit,65536)),T):
        if i.mnemonic in TERM_MN:return True,i.address+i.size-T
    return False,None

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe=RawPE();t=pe.byname[".text"];TLO=pe.imagebase+t["va"];THI=TLO+t["vsize"]
    sw=Sweep(pe,TLO,THI);at=Atlas()
    cov=load(COVERAGE);probe=load(PROBE);outside=load(OUTSIDE)
    adj=cov|probe|outside
    # read adjudication full
    import csv
    rows=[]
    with open(os.path.join(os.path.dirname(HERE),"EVIDENCE","ADJUDICATION_FULL.tsv"),encoding="utf-8") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    func=[r for r in rows if r["verdict"]=="FUNC"]
    print("total FUNC:",len(func))
    # classify by c4a/c4b evidence: recheck first byte
    cnt=collections.Counter()
    d_c4a_only=d_c4b_only=d_both=0
    a_c4a=a_c4b=0
    for r in func:
        A=int(r["addr"],16)
        data=pe.read(A,4)
        c4a=(data[0]==0x55 or data[:2] in (b"\x83\xec",b"\x81\xec"))
        c4b=leaf(data)
        ch=r["chan"]
        if "D" in ch:
            if c4a and c4b:d_both+=1
            elif c4a:d_c4a_only+=1
            elif c4b:d_c4b_only+=1
            else:cnt["D_neither"]+=1
        if "A" in ch:
            if c4a:a_c4a+=1
            elif c4b:a_c4b+=1
            else:cnt["A_neither"]+=1
    print("D-channel FUNC: c4a_only=%d c4b_only=%d both=%d other=%d"%(d_c4a_only,d_c4b_only,d_both,cnt["D_neither"]))
    print("A-channel FUNC: c4a=%d c4b=%d neither=%d"%(a_c4a,a_c4b,cnt["A_neither"]))

    # baseline test: among 16-aligned, prev-term, non-atlas, NOT-adjudicated addresses that FAIL c4a,
    # what fraction pass leaf(c4b)? And among RANDOM 16-aligned not-atlas addresses?
    prevok_no_c4a=[]; prevok_c4b=0
    for A in range((TLO+15)&~15,THI,16):
        if at.in_atlas(A):continue
        pr=predecessor(pe,sw,A)
        if pr["kind"] not in TERM_KINDS:continue
        raw=pe.read(A,3)
        if not raw:continue
        c4a=(raw[0]==0x55 or raw[:2] in (b"\x83\xec",b"\x81\xec"))
        if c4a:continue
        first=disasm_at(pe,A,n=1,span=16)
        if not first or first[0][0] in JCC or first[0][0]==".byte":continue
        prevok_no_c4a.append(A)
        if leaf(raw):prevok_c4b+=1
    print("baseline: 16-align+prev-term+nonJCC+NOT-c4a = %d; of those leaf(c4b)=%d (%.1f%%)"%(
        len(prevok_no_c4a),prevok_c4b,100*prevok_c4b/max(1,len(prevok_no_c4a))))

    random.seed(1)
    aligned=[A for A in range((TLO+15)&~15,THI,16) if not at.in_atlas(A)]
    rs=random.sample(aligned,2000)
    rleaf=sum(1 for A in rs if leaf(pe.read(A,3)))
    print("baseline: random 2000 16-align not-atlas: leaf= %d (%.1f%%)"%(rleaf,100*rleaf/2000))

    # check A-channel FUNC: are they rel32 targets? what are their addresses
    print("\nSample A-channel FUNC (20):")
    af=[r for r in func if "A" in r["chan"]]
    for r in af[:20]:
        print(" ",r["addr"],"c1=%s c2=%s c3=%s body=%s sem=%s/%s/%s"%(r["c1"],r["c2"],r["c3"],r["body"],r["sem1"],r["sem2"],r["sem3"]))

if __name__=="__main__":main()
