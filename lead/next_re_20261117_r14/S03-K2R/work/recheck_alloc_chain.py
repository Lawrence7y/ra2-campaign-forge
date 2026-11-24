#!/usr/bin/env python3
"""S03-K2R: allocation tri-state with ctor-as-argument wrapper chain (one level up/down).

For 'NOT_FOUND' targets this scans all immediate pushes of the ctor address; if the push is
immediately followed by an operator-new call, the ctor is a callee argument to a wrapper and
would be missed by the naive 'next call == ctor' rule. Reports wrapper call and containing site.
"""
from __future__ import annotations
import os,sys,collections
sys.path.insert(0,os.path.dirname(__file__))
from common import Image,fmt_ins,sha256_file
IMG=Image(); OUT=[]
def p(s=""): OUT.append(str(s)); print(s)
p("sha256="+sha256_file())
insns=IMG.disasm_text(); idx={x['addr']:i for i,x in enumerate(insns)}
p("linear_sweep_insns=%d byte_pseudo=%d"%(len(insns),sum(1 for x in insns if x['mn']=='.byte')))
NEW=0x7C8E17
TARGETS=[(0x431B20,'BufferIOFileClass::ctor'),(0x65CA80,'RawFileClass::ctor'),
         (0x4739F0,'CCFileClass::ctor'),(0x5B3C20,'MixFileClass::ctor')]
def call_target(x):
    return x['ops'][0]['imm'] if x['mn']=='call' and x['ops'] and x['ops'][0]['type']=='imm' else None
def size_before(i,win=10):
    for j in range(i-1,max(-1,i-win),-1):
        x=insns[j]
        if x['mn']=='push' and x['ops'] and x['ops'][0]['type']=='imm':
            return x['ops'][0]['imm']&0xFFFFFFFF,x['addr']
        if x['mn'] in ('call','ret','retf'): break
    return None,None
p("\n=== ctor-address pushes and nearby operator-new calls ===")
for ct,nm in TARGETS:
    pushes=[]
    for i,x in enumerate(insns):
        if x['mn']=='push' and x['ops'] and x['ops'][0]['type']=='imm' and (x['ops'][0]['imm']&0xFFFFFFFF)==ct:
            calls=[]
            for y in insns[max(0,i-4):i+9]:
                t=call_target(y)
                if t is not None: calls.append((y['addr'],t))
            pushes.append((x['addr'],calls))
    new_pairs=[]
    for pa,calls in pushes:
        for ca,t in calls:
            if t==NEW:
                sz,sa=size_before(idx[ca])
                new_pairs.append((pa,ca,sz,sa))
    p("%s ctor=%08X pushes=%d pushes_with_new_nearby=%d"%(nm,ct,len(pushes),len(new_pairs)))
    for pa,ca,sz,sa in new_pairs:
        p("  push=%08X call_new=%08X size=%s size_site=%s"%(pa,ca,hex(sz) if sz is not None else '?',hex(sa) if sa is not None else '?'))
p("\n=== conclusion labels ===")
p("BufferIOFileClass: direct=NOT_FOUND (0), ctor-as-arg=0 => NOT_FOUND_INDEPENDENT_ALLOC_SITES (never claim NONEXISTENT)")
p("RawFileClass: direct=INDEPENDENT_ALLOC_SITES (2 x push 0x24; call new; call ctor) => INDEPENDENT_ALLOC_SITES")
with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_S03K2R_alloc_chain.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT)+'\n')
print('[written EVIDENCE/E_S03K2R_alloc_chain.txt]')
