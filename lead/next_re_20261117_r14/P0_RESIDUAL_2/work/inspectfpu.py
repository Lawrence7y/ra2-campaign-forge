#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect FPU-byte pool\cov candidates + check vtable slot membership (槽值即函数)."""
import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *
pe=PE(); sw=Sweep(pe); at=Atlas()
cov=load_set(COVERAGE)
pool=[]
for va in range((pe.tlo+15)//16*16,pe.thi,16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
gapc=[a for a in pool if a not in cov]

# vtable slots from .rdata (COL-verified, per discipline: 槽值即函数)
r=pe.secs[".rdata"]; buf=pe.data[r["raw"]:r["raw"]+r["rawsize"]]
nw=len(buf)//4; words=struct.unpack_from("<%dI"%nw,buf,0)
def col_name(colp):
    if not (pe.IB<=colp<pe.IB+0x796000): return None
    d=pe.try_read(colp,16)
    if len(d)<16: return None
    sig,off,cd,tdp=struct.unpack("<IIII",d)
    if sig not in (0,1): return None
    nm=pe.try_read(tdp+8,200) if (pe.IB<=tdp<pe.IB+0x796000) else b""
    if not nm: return None
    z=nm.find(b"\0"); nm=nm[:z] if z>0 else nm
    return nm if nm.startswith((b".?AV",b".?AU")) else None
runs=[]; i=0
while i<nw:
    if pe.tlo<=words[i]<pe.thi:
        j=i
        while j<nw and pe.tlo<=words[j]<pe.thi: j+=1
        runs.append((i,j)); i=j
    else: i+=1
vt_all=set(); vt_col=set()
for i,j in runs:
    colp=words[i-1] if i>=1 else 0
    cls=col_name(colp)
    for w in words[i:j]:
        vt_all.add(w)
        if cls: vt_col.add(w)
print("vtable runs=%d slots(all)=%d COL-verified slots=%d"%(len(runs),len(vt_all),len(vt_col)))
print("pool\\cov in any vt run=%d ; in COL vt=%d"%(
    sum(1 for a in gapc if a in vt_all),sum(1 for a in gapc if a in vt_col)))

# FPU-first candidates: inspect a sample
fpu=[a for a in gapc if (pe.byte(a) in (0xDD,0xDB))]
print("\nFPU-first pool\\cov n=%d; sample:"%len(fpu))
for a in fpu[:12]:
    d=pe.try_read(a,24)
    pred=sw.endmap.get(a)
    # is it a sweep start? (capstone decoded there)
    iss = sw.index_of(a)>=0
    ii=next(md32(True).disasm(d,a),None)
    s=(ii.mnemonic+' '+ii.op_str) if ii else '?'
    print("  %08X pred=%-5s sweepstart=%s bytes=%s first=%s"%(a,pred or '?',iss,d[:12].hex(),s))
