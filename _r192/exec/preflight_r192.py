#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot R192 preflight: enumeration counts + thunk/jump shape samples."""
import sys, os, struct, collections
ROOT='/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT+'/_r185')
import pe185 as P
import capstone
from capstone.x86 import X86_OP_IMM

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]={'mdisp':w[i],'pTD':w[i+1],'pCHD':w[i+2],'name':nm.decode('latin1')}
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
group=collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]]['name']].append(vt)
def is_adj(a):
    o=P.r2o(a)
    if o is None: return False
    b=P.RAW[o:o+4]
    return (b[:3]==b'\x83\x6c\x24' or b[:3]==b'\x81\x6c\x24') and b[3]==4
direct=[]; adj=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        (adj if is_adj(v) else direct).append((vt,k,v))
print('PRE T1 COL=%d T2 VT=%d T3 slots=%d T4 groups=%d multi=%d T5 nonslots=%d adj=%d direct=%d'%(
    len(COL),len(VT),sum(NS.values()),len(group),sum(1 for x in group.values() if len(x)>1),
    sum(NS[v] for v in VT if COL[VT[v]]['mdisp']!=0),len(adj),len(direct)))

md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
cache={}
def jmpinfo(a):
    if a in cache: return cache[a]
    o=P.r2o(a); r=None
    if o is not None:
        ins=[]
        for it in md.disasm(P.RAW[o:o+32],a):
            ins.append((it.mnemonic,it.op_str,it.bytes.hex(),
                        [(op.type,op.imm) for op in it.operands]))
            if len(ins)>=8: break
        jt=[x for x in ins if x[0].startswith('jmp')]
        r=(ins,jt)
    cache[a]=r; return r
print('--- adjuster samples (first 12 unique) ---')
seen=set()
for vt,k,v in adj:
    if v in seen: continue
    seen.add(v)
    ins,jt=jmpinfo(v)
    print(hex(v), P.RAW[P.r2o(v):P.r2o(v)+16].hex(), '|', ' ; '.join(x[0]+' '+x[1]+' ['+x[2]+']' for x in ins[:4]), '| jmpimm=', [x[3] for x in jt])
    if len(seen)>=12: break
print('--- direct target samples (first 8 unique) ---')
seen=set()
for vt,k,v in direct:
    if v in seen: continue
    seen.add(v)
    b=P.RAW[P.r2o(v):P.r2o(v)+16]
    print(hex(v), b.hex(), '|', b[:2].hex(), 'E9' if b[0]==0xE9 else ('FF25' if b[:2]==b'\xff\x25' else '-'))
    if len(seen)>=8: break
print('--- four addresses ---')
for a in (0x410450,0x410580,0x410590,0x4C9150):
    o=P.r2o(a); b=P.RAW[o:o+32]
    ins,jt=jmpinfo(a)
    print(hex(a),b.hex(),'|',' ; '.join(x[0]+' '+x[1]+' ['+x[2]+']' for x in ins[:12]),'| jmpimm=',[x[3] for x in jt])
# E9/FF25 landing stats across direct targets
hits=collections.Counter()
for vt,k,v in direct:
    o=P.r2o(v); b=P.RAW[o:o+6]
    hits['E9' if b[0]==0xE9 else ('FF25' if b[:2]==b'\xff\x25' else 'OTHER')]+=1
print('direct-target heads',dict(hits))
