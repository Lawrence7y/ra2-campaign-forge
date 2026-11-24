#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ5 FINAL v2 adjudication: integrates jcc-target negative evidence (body-label detector)."""
import json, pickle, random, csv, hashlib
from collections import Counter
from pathlib import Path
import capstone
from engine import Bin

ROOT=Path(r'D:\Project\ra2-campaign-forge')
CARD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5'
WD=CARD/'work'; EVID=CARD/'EVIDENCE'
idx=pickle.load(open(WD/'idx.pkl','rb')); calls=idx['calls']; jmps=idx['jmps']; vtgt=idx['vtgt']
jidx=pickle.load(open(WD/'jcc_idx.pkl','rb')); jcc_tgt=jidx['jcc_tgt']; jmp_tgt=jidx['jmp_tgt']
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
                return (False, f'prev={ins.mnemonic}@{s:X}')
            if ins.address>=pe: break
    return (False, f'no-terminator(pad={npad})')

def leaf_body(va,maxb=96):
    chunk=bin_.read(va,maxb)
    if not chunk: return (False,'unreadable')
    n=0
    for ins in md.disasm(chunk,va):
        if ins.id==0: return (False,'data-byte')
        n+=1
        if ins.mnemonic in ('ret','retf'):
            return (False,'bare-ret epilogue') if n==1 else (True,f'{n}insn->ret@{ins.address:X}')
        if ins.mnemonic=='jmp' and ins.op_str.startswith('0x'):
            return (False,f'jmp-out@{ins.address:X}')
        if n>40: return (False,'body>40insn')
    return (False,'no-ret-96B')

def features(va):
    hb,he=hard_boundary(va); lb,le=leaf_body(va)
    return dict(va=va, a_call=va in calls, a_jmp=va in jmps, b_vt=va in vtgt,
                jcc=va in jcc_tgt, jmp_t=va in jmp_tgt, c=hb, c_ev=he, d=lb, d_ev=le)

def verdict(f):
    va=f['va']
    if f['a_call']:
        return ('FUNC','a',f"E8-call sites={','.join(hex(x) for x in calls[va][:3])}",'N')
    if f['b_vt']:
        return ('FUNC','b','vt-slot '+ ';'.join(s[0] for s in vtgt[va][:2]),'N')
    if f['jcc'] or f['jmp_t']:
        # internal branch destination = function-body label (shared epilogue / mid-body)
        src=jcc_tgt.get(va,[]) or jmp_tgt.get(va,[])
        return ('NOT_FUNC','label',f"jcc/jmp target from {','.join(hex(x) for x in src[:2])} => body-label",'-')
    if f['c'] and f['d']:
        return ('FUNC','c',f"c:{f['c_ev']} | d:{f['d_ev']} | no-branch-in",'Y')
    if f['a_jmp']:
        return ('NOT_FUNC','a',f"E9-jmp(weak) + no self-consistent body; c:{f['c_ev']} d:{f['d_ev']}",'-')
    return ('NOT_FUNC','c' if f['c'] else ('d' if f['d'] else '-'),f"c:{f['c_ev']} | d:{f['d_ev']}",'-')

addrs=sorted({int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()})
assert len(addrs)==1669
first=addrs[:100]
F100=[features(a) for a in first]; V100=[verdict(f) for f in F100]
func100=sum(1 for v in V100 if v[0]=='FUNC'); not100=100-func100
struct100=sum(1 for v in V100 if v[3]=='Y')
ptype=Counter(v[1] for v in V100 if v[0]=='FUNC')
ntype=Counter(v[1] for v in V100 if v[0]=='NOT_FUNC')

ridx=random.Random(20261119).sample(range(1669),100)
vr=[verdict(features(addrs[i])) for i in ridx]; func_pool=sum(1 for v in vr if v[0]=='FUNC')
t=bin_.text; lo=(t['va']+15)//16*16; hi=(t['va']+t['vsize'])//16*16; nal=(hi-lo)//16
gaddrs=[lo+16*i for i in random.Random(20261119).sample(range(nal),100)]
vg=[verdict(features(a)) for a in gaddrs]; func_glob=sum(1 for v in vg if v[0]=='FUNC')
# controls
atlas=[]
for line in open(ROOT/r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8',errors='replace').read().splitlines()[1:]:
    pp=line.split('\t')
    if pp and pp[0]: atlas.append(int(pp[0],16))
firstset=set(first); pos=[a for a in atlas if a in calls and a not in firstset][:5]
neg=[]
for row in csv.DictReader(open(ROOT/r'lead\next_re_20261117_r14\P0_RESIDUAL\EVIDENCE\ADJUDICATION_FULL.tsv',encoding='utf-8',newline=''),delimiter='\t'):
    if row['verdict'].strip()=='NOT_FUNC' and row['subkind'].strip()=='internal_label':
        neg.append(int(row['addr'],16))
neg=sorted(set(neg))[:5]
pos_v=[verdict(features(a))[0] for a in pos]; neg_v=[verdict(features(a))[0] for a in neg]
pos_pass=sum(1 for v in pos_v if v=='FUNC'); neg_pass=sum(1 for v in neg_v if v=='NOT_FUNC')

print('FUNC100',func100,'NOT100',not100,'struct_only',struct100,'ptype',dict(ptype),'ntype',dict(ntype))
print('pool_rand FUNC',func_pool,'global_rand FUNC',func_glob)
print('pos',pos_pass,'neg',neg_pass)
print('STOP func%',func100,'pool_delta_pp',abs(func100-func_pool))
# audit agreement on the 5 audited rows
aud={0x402F80:'NOT_FUNC',0x405AB0:'NOT_FUNC',0x4063A0:'NOT_FUNC',0x40A600:'NOT_FUNC',0x407080:'NOT_FUNC'}
agree=0
for a,exp in aud.items():
    got=verdict(features(a))[0]; agree+=(got==exp)
    print(f'audit {a:08X}: exp={exp} got={got}')
print('audit agreement',agree,'/5')

# ---------- deliverables ----------
with open(CARD/'ADJ_100.tsv','w',encoding='utf-8',newline='') as f:
    f.write('address\tverdict\tprimary_type\tkey_evidence\tstructural_only_only\n')
    for a,ff,vv in zip(first,F100,V100):
        f.write(f"{a:08X}\t{vv[0]}\t{vv[1]}\t{vv[2]}\t{vv[3]}\n")
TAG='（P0 入口闭合用；归属待 P1，不计入任何子系统百分比）'
with open(CARD/'coverage_delta.tsv','w',encoding='utf-8',newline='') as f:
    for a,ff,vv in zip(first,F100,V100):
        if vv[0]!='FUNC': continue
        e=f'{a:08X}'
        f.write(f"{e}\tS22\tsub_{e}\t[静态推断] 结构证据入口（前驱硬终止+自洽叶体+非分支目的，主判据={vv[1]}）；语义未证 {TAG}\t静态推断\tEVIDENCE/ADJ_100.tsv#{e}\n")
with open(EVID/'adjudication_detail.tsv','w',encoding='utf-8',newline='') as f:
    f.write('address\ta_call\ta_jmp\tb_vt\tjcc_target\tjmp_target\thard_boundary\tboundary_ev\tleaf_body\tleaf_ev\tverdict\tprimary\tstruct_only\n')
    for a,ff,vv in zip(first,F100,V100):
        f.write(f"{a:08X}\t{int(ff['a_call'])}\t{int(ff['a_jmp'])}\t{int(ff['b_vt'])}\t{int(ff['jcc'])}\t{int(ff['jmp_t'])}\t{int(ff['c'])}\t{ff['c_ev']}\t{int(ff['d'])}\t{ff['d_ev']}\t{vv[0]}\t{vv[1]}\t{vv[3]}\n")

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as fh:
        for b in iter(lambda:fh.read(1<<20),b''): h.update(b)
    return h.hexdigest().upper()
summary=dict(
 dedup=dict(undecidable=5598,in_coverage=3929,not_in_coverage=1669),
 first100=dict(func=func100,not_func=not100,structural_only=struct100,func_primary=dict(ptype),not_primary=dict(ntype)),
 baselines=dict(pool_rand_seed20261119_func=func_pool,global_rand_func=func_glob),
 controls=dict(pos_pass=pos_pass,neg_pass=neg_pass,pos=[f'{a:08X}' for a in pos],neg=[f'{a:08X}' for a in neg]),
 primary_absence=dict(a_call_pool=sum(1 for a in addrs if a in calls),a_jmp_pool=sum(1 for a in addrs if a in jmps),b_vt_pool=sum(1 for a in addrs if a in vtgt),jcc_target_pool=sum(1 for a in addrs if a in jcc_tgt)),
 audit_agreement=agree,
 stop=dict(func_pct=func100,pool_delta_pp=abs(func100-func_pool)),
 sha=dict(enum=sha(ROOT/r'lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv'),
          coverage=sha(ROOT/r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),
          gamemd=sha(ROOT/r'ra2youli\gamemd.exe')))
json.dump(summary,open(WD/'summary.json','w',encoding='utf-8'),indent=2,ensure_ascii=False)
print('wrote deliverables')
