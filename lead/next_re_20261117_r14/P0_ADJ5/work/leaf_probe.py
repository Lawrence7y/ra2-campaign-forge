#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find a NON-circular structural (c): hard boundary + self-contained leaf body."""
import pickle, capstone, random
from collections import Counter
from pathlib import Path
from engine import Bin
ROOT=Path(r'D:\Project\ra2-campaign-forge')
WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
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
                return (ins.mnemonic in HARD or ins.bytes[0] in B0HARD)
            if ins.address>=pe: break
    return False

def leaf_body(va,maxb=96):
    """True if from va a linear decode reaches a ret within maxb bytes, no unconditional jmp out,
       and at least 1 instruction; false if first insn is a bare ret (shared epilogue) or falls through."""
    chunk=bin_.read(va,maxb)
    if not chunk: return (False,'unreadable')
    n=0; first=None
    for ins in md.disasm(chunk,va):
        if ins.id==0: return (False,'data-byte')
        if first is None: first=ins.mnemonic
        n+=1
        if ins.mnemonic in ('ret','retf'):
            if n==1: return (False,'bare-ret epilogue')
            return (True,f'{n}insn ret@{ins.address:X}')
        if ins.mnemonic=='jmp' and ins.op_str.startswith('0x'):
            return (False,f'jmp-out@{ins.address:X}')
        if n>40: return (False,'too-long')
    return (False,'no-ret-in-window')

def full(va):
    hb=hard_boundary(va)
    lb,lev=leaf_body(va)
    return hb,lb,lev

addrs=sorted({int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()})
F=[full(a) for a in addrs]
print('FULL POOL:',Counter((h,l) for h,l,_ in F))

sets={
 'first100':list(range(100)),
 'pool_rand100':random.Random(20261119).sample(range(1669),100),
}
for name,idx in sets.items():
    sub=[F[i] for i in idx]
    print(name,'hard&leaf=',sum(1 for h,l,_ in sub if h and l),
          'hard_only=',sum(1 for h,l,_ in sub if h and not l),
          'hard%=',round(100*sum(1 for h,_,_ in sub if h)/len(sub),1))
# global
t=bin_.text; lo=(t['va']+15)//16*16; hi=(t['va']+t['vsize'])//16*16; nal=(hi-lo)//16
g=[lo+16*i for i in random.Random(20261119).sample(range(nal),100)]
GF=[full(a) for a in g]
print('global_rand100 hard&leaf=',sum(1 for h,l,_ in GF if h and l),
      'hard%=',round(100*sum(1 for h,_,_ in GF if h),1))

# save classification
with open(WD/'struct_class.tsv','w',encoding='utf-8') as f:
    f.write('va\thard_boundary\tleaf_body\tdetail\n')
    for a,(h,l,e) in zip(addrs,F):
        f.write(f'{a:08X}\t{int(h)}\t{int(l)}\t{e}\n')
print('wrote struct_class.tsv')
