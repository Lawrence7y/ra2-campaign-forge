#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final P0-ADJ5 adjudication engine + baselines + controls.

CRITERION (declared, atlas-independent):
  PRECONDITIONS (ENUM pool definition, NOT counted as criteria):
    align16 ; coarse predecessor in {nop,ret,jmp,int3} ; first byte not in {E8,E9,EB}.
  PRIMARY:
    (a) instruction-boundary E8 call rel32 target (strong) / E9 jmp rel32 target (weak, 错源②);
    (b) slot value of an RTTI-resolvable vtable.
  SUPPORTING:
    (c) STRICT boundary proof: decode backward from va; through <=15 nop/int3 pad bytes,
        require a real ret/retf/jmp/int3/hlt/ud2 instruction ending immediately before pad/va.
    (d) standard prologue (push ebp;mov ebp,esp | sub esp,imm) + body to a ret.
  VERDICT: FUNC if (a)|(b) [structural_only=N]; else FUNC if (c)|(d) [structural_only=Y];
           else NOT_FUNC.
"""
import struct, json, pickle, random, csv
from pathlib import Path
from engine import Bin, prologue, in_text, rtti_name

ROOT=Path(r'D:\Project\ra2-campaign-forge')
WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
idx=pickle.load(open(WD/'idx.pkl','rb'))
calls=idx['calls']; jmps=idx['jmps']; vtgt=idx['vtgt']
bin_=Bin()

TERM_MNEM={'ret','retf','jmp','int3','hlt','ud2'}
TERM_B0={0xC3,0xC2,0xEB,0xE9,0xEA,0xCB,0xCA,0xCC,0xF4}

import capstone
def strict_boundary(va):
    """(c) true function-ending proof: <=15 pad bytes (0x90/0xCC) immediately before va,
       then a real terminator instruction ending exactly at the pad start (or at va if no pad).
       Returns (bool, evidence)."""
    # count pad bytes immediately before va
    npad=0
    while npad<16:
        b=bin_.u8(va-1-npad)
        if b in (0x90,0xCC): npad+=1
        else: break
    pad_end=va-npad  # terminator must end here
    # decode a terminator ending exactly at pad_end, scanning starts up to 12 bytes back
    md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=False; md.skipdata=True
    for start in range(pad_end-12, pad_end):
        if start < bin_.text['va']: continue
        seg=bin_.read(start, pad_end-start+4)
        if not seg: continue
        for insn in md.disasm(seg, start):
            if insn.id==0: continue
            if insn.address+insn.size==pad_end:
                if insn.mnemonic in TERM_MNEM or insn.bytes[0] in TERM_B0:
                    return (True, f'{"pad"+str(npad)+"x90/CC;" if npad else ""}{insn.mnemonic}@{start:X}+{insn.size}')
                break
            if insn.address>=pad_end: break
    return (False, f'no-terminator(pad={npad})')

def features(va):
    a_call=va in calls
    a_jmp=va in jmps
    b_vt=va in vtgt
    cb,ce=strict_boundary(va)
    db,de=prologue(bin_,va)
    return dict(va=va,a_call=a_call,a_jmp=a_jmp,b_vt=b_vt,c=cb,c_ev=ce,d=db,d_ev=de)

def verdict(f):
    if f['a_call']:
        return ('FUNC','a',f"E8 call target; sites={','.join(hex(x) for x in calls[f['va']][:3])}",'N')
    if f['b_vt']:
        slots=vtgt[f['va']][:2]
        return ('FUNC','b','vtable slot '+ ';'.join(s[0] for s in slots),'N')
    if f['a_jmp']:
        # E9 jmp target: weak per 错源② (jmp32 true-entry only 2/78) -> supporting only
        base=('jmp-target(E9,weak)','a',f"E9 jmp target sites={','.join(hex(x) for x in jmps[f['va']][:3])}")
        if f['c']:
            return ('FUNC','a',base[2]+'; '+f['c_ev'],'Y')
        if f['d']:
            return ('FUNC','a',base[2]+'; '+f['d_ev'],'Y')
        return ('NOT_FUNC','a',base[2]+'; no boundary/prologue','-')
    if f['c']:
        return ('FUNC','c',f['c_ev'],'Y')
    if f['d']:
        return ('FUNC','d',f['d_ev'],'Y')
    return ('NOT_FUNC','-','no a/b; no strict boundary; no prologue','-')

# ---- load 1669 ----
addrs=sorted({int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()})
assert len(addrs)==1669

# ---- first 100 (ascending) ----
first=addrs[:100]
f100=[features(a) for a in first]
v100=[verdict(f) for f in f100]
func100=sum(1 for v in v100 if v[0]=='FUNC')
not100=100-func100
struct100=sum(1 for v in v100 if v[3]=='Y')
# primary-type distribution
from collections import Counter
ptype=Counter(v[1] for v in v100 if v[0]=='FUNC')

# ---- pool random 100 seed 20261119 ----
rng=random.Random(20261119)
pool_idx=rng.sample(range(1669),100)
pool_rand=[addrs[i] for i in pool_idx]
vr=[verdict(features(a)) for a in pool_rand]
func_pool=sum(1 for v in vr if v[0]=='FUNC')

# ---- global random 100 16B-aligned in .text ----
t=bin_.text
lo=(t['va']+15)//16*16
hi=(t['va']+t['vsize'])//16*16
nal=(hi-lo)//16
gidx=random.Random(20261119).sample(range(nal),100)
gaddrs=[lo+16*i for i in gidx]
vg=[verdict(features(a)) for a in gaddrs]
func_glob=sum(1 for v in vg if v[0]=='FUNC')

# ---- controls ----
# positive: 5 atlas entries with call target, none in first100
atlas=[]
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
for line in open(p,encoding='utf-8',errors='replace').read().splitlines()[1:]:
    pp=line.split('\t')
    if pp and pp[0]: atlas.append(int(pp[0],16))
pos=[a for a in atlas if a in calls and a not in set(first)][:5]
# negative: 5 P0_RESIDUAL NOT_FUNC internal_label deterministic ascending
neg=[]
p2=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL\EVIDENCE\ADJUDICATION_FULL.tsv'
for row in csv.DictReader(open(p2,encoding='utf-8',newline=''),delimiter='\t'):
    if row['verdict'].strip()=='NOT_FUNC' and row['subkind'].strip()=='internal_label':
        neg.append(int(row['addr'],16))
neg=sorted(set(neg))[:5]
pos_v=[verdict(features(a))[0] for a in pos]
neg_v=[verdict(features(a))[0] for a in neg]
pos_pass=sum(1 for v in pos_v if v=='FUNC')
neg_pass=sum(1 for v in neg_v if v=='NOT_FUNC')

print('=== THREE DEDUP ===', 5598,3929,1669)
print('=== FIRST100 === FUNC',func100,'NOT_FUNC',not100,'struct_only',struct100,'FUNC-rate',func100,'ptypes',dict(ptype))
print('=== POOL RANDOM100 === FUNC',func_pool,'rate%',func_pool)
print('=== GLOBAL RANDOM100 === FUNC',func_glob,'rate%',func_glob)
print('=== CONTROLS === pos',[(f'{a:08X}',v) for a,v in zip(pos,pos_v)],'pass',pos_pass,'/5')
print('=== CONTROLS === neg',[(f'{a:08X}',v) for a,v in zip(neg,neg_v)],'pass',neg_pass,'/5')
print('=== STOP CHECK === FUNC%',func100,'; pool delta pp',abs(func100-func_pool))

# dump verdicts for first100
with open(WD/'v100.tsv','w',encoding='utf-8') as f:
    f.write('idx\taddress\tverdict\tprimary_type\tevidence\tstruct_only\ta_call\ta_jmp\tb_vt\tc\td\n')
    for i,(a,ff,vv) in enumerate(zip(first,f100,v100)):
        f.write(f'{i}\t{a:08X}\t{vv[0]}\t{vv[1]}\t{vv[2]}\t{vv[3]}\t{int(ff["a_call"])}\t{int(ff["a_jmp"])}\t{int(ff["b_vt"])}\t{int(ff["c"])}\t{int(ff["d"])}\n')

# save summary json
summary=dict(dedup=[5598,3929,1669],func100=func100,not100=not100,struct100=struct100,
             ptypes=dict(ptype),pool_func=func_pool,global_func=func_glob,
             pos_pass=pos_pass,neg_pass=neg_pass,
             pos=[f'{a:08X}' for a in pos],neg=[f'{a:08X}' for a in neg],
             a_call_any=sum(1 for a in addrs if a in calls),
             a_jmp_any=sum(1 for a in addrs if a in jmps),
             b_vt_any=sum(1 for a in addrs if a in vtgt))
json.dump(summary,open(WD/'summary.json','w',encoding='utf-8'),indent=2)
print('wrote v100.tsv and summary.json')
