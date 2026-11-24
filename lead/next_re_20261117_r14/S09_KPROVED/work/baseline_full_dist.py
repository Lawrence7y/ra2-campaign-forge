#!/usr/bin/env python3
"""Emit exact 2000-trial distribution for the full ③b detector (P1/P2/P3/P4), seed 20261119."""
import csv,random,os
CLASS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\EVIDENCE'
base={x['entry']:x for x in csv.DictReader(open(os.path.join(EV,'pool_3b_flags.tsv'),encoding='utf-8'),delimiter='\t')}
# full flag: use p3 result recomputed inline from a saved sidecar we write here
# (baseline_p3 already computed; replicate its per-entry b3_full via a tiny recompute of p3 flag)
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True);IB=pe.OPTIONAL_HEADER.ImageBase;D=pe.__data__
SEC=[(s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData) for s in pe.sections]
def off(va):
    r=va-IB
    for v,sz,p in SEC:
        if v<=r<v+sz:return p+(r-v)
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
rows=[r for r in csv.DictReader(open(CLASS,encoding='utf-8'),delimiter='\t') if r['subsystem']=='S09']
def p3(r):
    lo=int(r['ext_lo'],16);hi=int(r['ext_hi'],16)
    if hi<=lo or hi-lo>20000:hi=lo+(int(r['atlas_size']) or 64)
    o=off(lo)
    if o is None:return False
    cs=set()
    for i in md.disasm(D[o:o+(hi-lo)],lo):
        if i.mnemonic=='cmp' and i.operands:
            for op in i.operands:
                if op.type==2 and op.imm not in (-1,0): cs.add(op.imm)
    return len(cs)>=3
hit={}
for r in rows:
    e=r['entry']; b3=base[e]['b3']=='1'; g=p3(r)
    hit[e]=(r['has4_strict']=='1' and (b3 or g))
rng=random.Random(20261119); ent=[r['entry'] for r in rows]
hs=[sum(hit[e] for e in rng.sample(ent,8)) for _ in range(2000)]
dist={h:hs.count(h) for h in sorted(set(hs))}
print('K=',sum(hit.values()),'N=',len(rows),'mean=',sum(hs)/2000)
print('dist=',dist)
