#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断脚本：精确计算 channel D (c1+c3+c4a|c4b) 与 c5/c6 排除，并核对各通道并集。"""
import os, sys, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from resid_common import (RawPE, Sweep, Atlas, md_new, COVERAGE, PROBE, OUTSIDE,
                          disasm_at, predecessor, trailing_pad, JCC, TERM_KINDS)

ITEMS_RANGES = [(0xA8EC7C, 0xA8EC80), (0xA8ECBC, 0xA8ECC0), (0xB0F4EC, 0xB0F4F0)]
TERM_MN = {"ret", "retn", "retf", "jmp"}
JT_SPAN = 0x1000

def load(p, col=0):
    s=set()
    with open(p,encoding="utf-8",errors="replace") as f:
        f.readline()
        for ln in f:
            if not ln.strip(): continue
            t=ln.rstrip("\n").split("\t")
            try: s.add(int(t[col],16))
            except: pass
    return s

def leaf_pattern(data):
    b=data
    if len(b)<3: return False
    if b[0]==0x8B and (b[1]&0xF0)==0x40 and b[2]==0x24: return True
    if b[0]==0x8B and b[1]==0x41: return True
    if b[0] in (0x57,0x56,0x53): return True
    return False

def body_term(pe,T,limit=4096):
    data=pe.read(T,min(limit,65536))
    for i in md_new().disasm(data,T):
        if i.mnemonic in TERM_MN:
            return True,(i.address+i.size-T)
    return False,None

def pointer_table(pe,T,n=6):
    ds=[]
    for k in range(n):
        try: ds.append(pe.u32(T+4*k))
        except: return False
    nt=sum(1 for d in ds if pe.in_text(d))
    span=max(ds)-min(ds) if nt==len(ds) else -1
    return nt==len(ds) and len(set(ds))>=5 and 0<=span<=JT_SPAN

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe=RawPE(); t=pe.byname[".text"]
    TLO=pe.imagebase+t["va"]; THI=TLO+t["vsize"]
    sw=Sweep(pe,TLO,THI); at=Atlas()
    cov=load(COVERAGE); probe=load(PROBE); outside=load(OUTSIDE)

    # rel32 targets (all, in .text) for sem2
    rel32=set()
    for i in range(sw.n):
        b=sw.bytes_list[i]
        if len(b)==5 and b[0] in (0xE8,0xE9):
            rel=struct.unpack("<i",b[1:5])[0]
            tgt=sw.starts[i]+5+rel
            if TLO<=tgt<THI: rel32.add(tgt)

    # channel D enumeration: 16-align, not atlas, prev term, non-JCC, c4a or c4b-leaf
    c4a=set(); c4b=set(); d_all=set()
    n_align=0; n_prevok=0
    for A in range((TLO+15)&~15, THI, 16):
        if at.in_atlas(A): continue
        n_align+=1
        pr=predecessor(pe,sw,A)
        if pr["kind"] not in TERM_KINDS: continue
        n_prevok+=1
        raw3=pe.read(A,3)
        if not raw3: continue
        first=disasm_at(pe,A,n=3,span=24)
        fmn=first[0][0] if first else ".byte"
        if fmn in JCC or fmn==".byte": continue
        is_c4a=(raw3[0]==0x55 or raw3[:2] in (b"\x83\xec",b"\x81\xec"))
        bt,bl=body_term(pe,A)
        is_c4b=bool(leaf_pattern(raw3) and bt and bl is not None and bl>=2)
        if is_c4a: c4a.add(A)
        if is_c4b: c4b.add(A)
        if is_c4a or is_c4b: d_all.add(A)
    print("align not-atlas:",n_align,"prev-ok:",n_prevok)
    print("c4a(prologue):",len(c4a),"c4b(leaf):",len(c4b),"union:",len(d_all))
    print("c4b not in c4a:",len(c4b-c4a))
    resid=d_all-cov-probe-outside
    print("channel D residual (minus cov/probe/outside):",len(resid))
    print("  c4a-only residual:",len((c4a-c4b)-cov-probe-outside))
    print("  c4b residual:",len(c4b-cov-probe-outside))
    # c5/c6
    jt=set(); cont=set()
    for A in resid:
        if pointer_table(pe,A): jt.add(A)
        if any(a<=A<b for a,b in ITEMS_RANGES): cont.add(A)
    print("  c5 jump-table fails:",len(jt),"c6 container fails:",len(cont))
    print("  final FUNC-candidate D:",len(resid-jt-cont))
    # breakdown of c4b residual by sem
    sem1_0=0
    for A in sorted(c4b-cov-probe-outside):
        pass

if __name__=="__main__":
    main()
