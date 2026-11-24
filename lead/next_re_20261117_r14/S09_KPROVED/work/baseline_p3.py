#!/usr/bin/env python3
"""Baseline with ③b detector including P3 multi-guard chain (D-42 细则#1), consistent
with manual verification of 004AB9B0. Reads EVIDENCE/pool_3b_flags.tsv + re-scans bodies
only for the P3 signal; reports ④∧③b expected hits in 8 random rows (seed 20261119, 2000x).
"""
import csv, struct, random, os, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
CLASS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\EVIDENCE'
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase; D=pe.__data__
SEC=[(s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData) for s in pe.sections]
def va2off(va):
    r=va-IB
    for v,sz,p in SEC:
        if v<=r<v+sz: return p+(r-v)
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
rows=[r for r in csv.DictReader(open(CLASS,encoding='utf-8'),delimiter='\t') if r['subsystem']=='S09']
base={x['entry']:x for x in csv.DictReader(open(os.path.join(EV,'pool_3b_flags.tsv'),encoding='utf-8'),delimiter='\t')}
def p3(r):
    lo=int(r['ext_lo'],16); hi=int(r['ext_hi'],16)
    if hi<=lo or hi-lo>20000: hi=lo+(int(r['atlas_size']) or 64)
    o=va2off(lo)
    if o is None: return False
    consts=set()
    for i in md.disasm(D[o:o+(hi-lo)],lo):
        if i.mnemonic=='cmp' and i.operands:
            for op in i.operands:
                if op.type==2 and op.imm not in (-1,0):  # X86_OP_IMM=2
                    consts.add(op.imm)
    return len(consts)>=3
flag={}
for r in rows:
    e=r['entry']
    b3=base[e]['b3']=='1'
    g=p3(r)
    flag[e]={'b3_strict':b3,'p3':g,'b3_full':b3 or g,'hit_strict':base[e]['hit']=='1',
             'hit_full':(r['has4_strict']=='1' and (b3 or g))}
for label,key in [('strict(P1/P2/P4)','hit_strict'),('full(+P3 multiguard)','hit_full')]:
    K=sum(1 for v in flag.values() if v[key]); N=len(rows); p=K/N
    rng=random.Random(20261119); hs=[sum(flag[e][key] for e in rng.sample([r['entry'] for r in rows],8)) for _ in range(2000)]
    print(f'{label}: K={K} N={N} p={p:.4f} analytic8p={8*p:.4f} emp={sum(hs)/2000:.4f}')
# check the 8
for e in ['004AAE90','005BDF70','006A5310','004AB9B0','0063FEA0','006A7780','004ACE70','006ABD30']:
    print(e, flag[e])
