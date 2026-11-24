#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ5 FINAL adjudication + baselines + controls + deliverables.

CRITERION (declared; atlas-independent):
  PRECONDITIONS (ENUM pool definition, NOT counted as criteria, zero within-pool power):
    align16 ; coarse predecessor in {nop,ret,jmp,int3} ; first byte not in {E8,E9,EB}.
  PRIMARY (required to be present; REPORTED honestly as 0-by-construction on this pool):
    (a) E8 call rel32 boundary target (strong) / E9 jmp rel32 boundary target (weak, 错源②).
    (b) RTTI-resolvable vtable slot value.
  SUPPORTING (the only evidence with purchase on this pool):
    (c) STRICT boundary: hard function terminator (ret/retf/int3/hlt/ud2), NOT jmp,
        ending <=15 pad bytes (90/CC) immediately before va.
    (d) body self-consistency: linear decode from va reaches a ret within 96 B with no
        unconditional jmp-out and >=2 insns (excludes bare-ret shared epilogues).
  VERDICT: FUNC if (a-strong)|(b) -> structural_only=N; else FUNC if (c)AND(d) -> structural_only=Y;
           else NOT_FUNC.  E9 jmp alone is weak (supporting) and does not by itself give FUNC.
"""
import struct, json, pickle, random, csv, hashlib
from collections import Counter
from pathlib import Path
import capstone
from engine import Bin

ROOT=Path(r'D:\Project\ra2-campaign-forge')
CARD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5'
WD=CARD/'work'; EVID=CARD/'EVIDENCE'
idx=pickle.load(open(WD/'idx.pkl','rb'))
calls=idx['calls']; jmps=idx['jmps']; vtgt=idx['vtgt']
bin_=Bin()
HARD={'ret','retf','int3','hlt','ud2'}; B0HARD={0xC3,0xC2,0xCC,0xF4,0xCB,0xCA}
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False; md.skipdata=True

def hard_boundary(va):
    npad=0
    while npad<16 and bin_.u8(va-1-npad) in (0x90,0xCC): npad+=1
    pe=va-npad
    for s in range(pe-12,pe):
        if s<bin_.text['va']: continue
        seg=bin_.read(s,pe-s+4)
        if not seg: continue
        for ins in md.disasm(seg,s):
            if ins.id==0: continue
            if ins.address+ins.size==pe:
                if ins.mnemonic in HARD or ins.bytes[0] in B0HARD:
                    return (True, f'{"pad"+str(npad)+"x90/CC;" if npad else ""}{ins.mnemonic}@{s:X}+{ins.size}')
                return (False, f'prev={ins.mnemonic}@{s:X} (not hard terminator)')
            if ins.address>=pe: break
    return (False, f'no-decoded-terminator(pad={npad})')

def leaf_body(va,maxb=96):
    chunk=bin_.read(va,maxb)
    if not chunk: return (False,'unreadable')
    n=0
    for ins in md.disasm(chunk,va):
        if ins.id==0: return (False,'data-byte-in-body')
        n+=1
        if ins.mnemonic in ('ret','retf'):
            if n==1: return (False,'bare-ret shared epilogue')
            return (True,f'{n}insn->ret@{ins.address:X}')
        if ins.mnemonic=='jmp' and ins.op_str.startswith('0x'):
            return (False,f'jmp-out@{ins.address:X}')
        if n>40: return (False,'body>40insn')
    return (False,'no-ret-in-96B')

def features(va):
    hb,he=hard_boundary(va); lb,le=leaf_body(va)
    return dict(va=va, a_call=va in calls, a_jmp=va in jmps, b_vt=va in vtgt,
                c=hb, c_ev=he, d=lb, d_ev=le)

def verdict(f):
    va=f['va']
    if f['a_call']:
        return ('FUNC','a',f"E8-call sites={','.join(hex(x) for x in calls[va][:3])}",'N')
    if f['b_vt']:
        return ('FUNC','b','vt-slot '+ ';'.join(s[0] for s in vtgt[va][:2]),'N')
    if f['c'] and f['d']:
        return ('FUNC','c',f"c:{f['c_ev']} | d:{f['d_ev']}",'Y')
    # not FUNC: record why / weak evidence
    if f['a_jmp']:
        return ('NOT_FUNC','a',f"E9-jmp(weak,错源②) sites={','.join(hex(x) for x in jmps[va][:2])}; c={f['c_ev']}; d={f['d_ev']}",'-')
    return ('NOT_FUNC','c' if f['c'] else ('d' if f['d'] else '-'),
            f"c:{f['c_ev']} | d:{f['d_ev']}",'-')

# ------------ data ------------
addrs=sorted({int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()})
assert len(addrs)==1669
first=addrs[:100]
F100=[features(a) for a in first]; V100=[verdict(f) for f in F100]
func100=sum(1 for v in V100 if v[0]=='FUNC'); not100=100-func100
struct100=sum(1 for v in V100 if v[3]=='Y')
ptype=Counter(v[1] for v in V100 if v[0]=='FUNC')

# pool random 100
ridx=random.Random(20261119).sample(range(1669),100)
vr=[verdict(features(addrs[i])) for i in ridx]
func_pool=sum(1 for v in vr if v[0]=='FUNC')
# global random 100 aligned
t=bin_.text; lo=(t['va']+15)//16*16; hi=(t['va']+t['vsize'])//16*16; nal=(hi-lo)//16
gidx=random.Random(20261119).sample(range(nal),100)
gaddrs=[lo+16*i for i in gidx]
vg=[verdict(features(a)) for a in gaddrs]
func_glob=sum(1 for v in vg if v[0]=='FUNC')
# controls
atlas=[]
for line in open(ROOT/r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8',errors='replace').read().splitlines()[1:]:
    pp=line.split('\t')
    if pp and pp[0]: atlas.append(int(pp[0],16))
firstset=set(first)
pos=[a for a in atlas if a in calls and a not in firstset][:5]
neg=[]
for row in csv.DictReader(open(ROOT/r'lead\next_re_20261117_r14\P0_RESIDUAL\EVIDENCE\ADJUDICATION_FULL.tsv',encoding='utf-8',newline=''),delimiter='\t'):
    if row['verdict'].strip()=='NOT_FUNC' and row['subkind'].strip()=='internal_label':
        neg.append(int(row['addr'],16))
neg=sorted(set(neg))[:5]
pos_v=[verdict(features(a))[0] for a in pos]; neg_v=[verdict(features(a))[0] for a in neg]
pos_pass=sum(1 for v in pos_v if v=='FUNC'); neg_pass=sum(1 for v in neg_v if v=='NOT_FUNC')

print('FUNC100',func100,'NOT100',not100,'struct_only',struct100,'ptype',dict(ptype))
print('pool_rand FUNC',func_pool,'global_rand FUNC',func_glob)
print('pos',[(f'{a:08X}',v) for a,v in zip(pos,pos_v)],pos_pass)
print('neg',[(f'{a:08X}',v) for a,v in zip(neg,neg_v)],neg_pass)
print('STOP: func%',func100,'pool_delta_pp',abs(func100-func_pool))

# ------------ ADJ_100.tsv ------------
with open(CARD/'ADJ_100.tsv','w',encoding='utf-8',newline='') as f:
    f.write('address\tverdict\tprimary_type\tkey_evidence\tstructural_only_only\n')
    for a,ff,vv in zip(first,F100,V100):
        f.write(f"{a:08X}\t{vv[0]}\t{vv[1]}\t{vv[2]}\t{vv[3]}\n")

# ------------ coverage_delta.tsv ------------
# format: entry(hex8) TAB subsystem TAB name TAB one_line_semantics TAB grade TAB evidence_path
TAG='（P0 入口闭合用；归属待 P1，不计入任何子系统百分比）'
with open(CARD/'coverage_delta.tsv','w',encoding='utf-8',newline='') as f:
    for a,ff,vv in zip(first,F100,V100):
        if vv[0]!='FUNC': continue
        entry=f'{a:08X}'; name='sub_'+entry
        sem=f"[静态推断] 结构证据入口（前驱硬终止+自洽叶体，主判据={vv[1]}）；语义未证 {TAG}"
        ev=f"EVIDENCE/ADJ_100.tsv#{entry}"
        f.write(f"{entry}\tS22\t{name}\t{sem}\t静态推断\t{ev}\n")

# ------------ EVIDENCE dumps ------------
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as fh:
        for b in iter(lambda:fh.read(1<<20),b''): h.update(b)
    return h.hexdigest().upper()
with open(EVID/'adjudication_detail.tsv','w',encoding='utf-8',newline='') as f:
    f.write('address\ta_call\ta_jmp\tb_vt\thard_boundary\tboundary_ev\tleaf_body\tleaf_ev\tverdict\tprimary\tstruct_only\n')
    for a,ff,vv in zip(first,F100,V100):
        f.write(f"{a:08X}\t{int(ff['a_call'])}\t{int(ff['a_jmp'])}\t{int(ff['b_vt'])}\t{int(ff['c'])}\t{ff['c_ev']}\t{int(ff['d'])}\t{ff['d_ev']}\t{vv[0]}\t{vv[1]}\t{vv[3]}\n")
# pool counters
flag_any_call=sum(1 for a in addrs if a in calls)
flag_any_jmp=sum(1 for a in addrs if a in jmps)
flag_any_vt=sum(1 for a in addrs if a in vtgt)
summary=dict(
    dedup=dict(undecidable=5598,in_coverage=3929,not_in_coverage=1669),
    first100=dict(func=func100,not_func=not100,structural_only=struct100,primary_types=dict(ptype)),
    baselines=dict(pool_rand_seed20261119_func=func_pool,global_rand_func=func_glob),
    controls=dict(pos_pass=pos_pass,neg_pass=neg_pass,pos=[f'{a:08X}' for a in pos],neg=[f'{a:08X}' for a in neg]),
    primary_absence=dict(a_call_pool=flag_any_call,a_jmp_pool=flag_any_jmp,b_vt_pool=flag_any_vt),
    stop=dict(func_pct=func100,pool_delta_pp=abs(func100-func_pool)),
    sha=dict(enum=sha(ROOT/r'lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv'),
             coverage=sha(ROOT/r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),
             gamemd=sha(ROOT/r'ra2youli\gamemd.exe')))
json.dump(summary,open(WD/'summary.json','w',encoding='utf-8'),indent=2,ensure_ascii=False)
print('wrote ADJ_100.tsv, coverage_delta.tsv, EVIDENCE, summary.json')
