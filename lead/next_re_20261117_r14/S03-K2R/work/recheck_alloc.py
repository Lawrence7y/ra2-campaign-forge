#!/usr/bin/env python3
"""S03-K2R: redo #6 embedded-base allocation tri-state scan.

Whole-image .text sweep with capstone(skipdata=True). For each target ctor, report independent
allocation sites found via multiple equivalent forms:
  1 push imm8/imm32 -> call 0x7C8E17 (operator new / thunk to 0x7C9442)
  2 mov ecx,imm -> call 0x7C8E17
  3 push imm followed by call to any direct thunk eventually targeting new/operator new
  4 call 0x7C8E17 with size from preceding mov reg,imm (reg-to-ecx accepted)
Output tri-state: 独立分配点 / 无分配点 / 未找到. "未找到" is never rendered "不存在".
"""
from __future__ import annotations
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import Image, fmt_ins, sha256_file

IMG=Image(); OUT=[]
def p(s=""):
    OUT.append(str(s)); print(s)

p("sha256="+sha256_file())
p("text=[0x%X,0x%X)" % (IMG.text_va,IMG.text_va+len(IMG.text_bytes)))
insns=IMG.disasm_text(); idx={x['addr']:i for i,x in enumerate(insns)}
p("linear_sweep_insns=%d byte_pseudo=%d" % (len(insns),sum(1 for x in insns if x['mn']=='.byte')))

# Direct operator new wrapper at 0x7C8E17; also known thunk/allocator targets.
NEW=0x7C8E17
NEW_THUNKS={0x7C8E17:'operator_new',0x7C9442:'_nh_malloc'}

# Target constructors for the 5 GetSize subjects (prior S03-K2 T3 list).
TARGETS=[
  (0x431B20,'BufferIOFileClass::ctor'),
  (0x65CA80,'RawFileClass::ctor'),
  (0x4739F0,'CCFileClass::ctor'),
  (0x5B3C20,'MixFileClass::ctor'),
  (0x47AA30,'CDFileClass::ctor_candidate_47AA30'),
  (0x47A9E0,'CDFileClass::ctor_candidate_47A9E0'),
]
# RawFileClass ctor also appears as v16 0x65CA70 thunk; keep both target labels.
TARGETS.append((0x65CA70,'RawFileClass::ctor_v16'))

def call_target(x):
    if x['mn']=='call' and x['ops'] and x['ops'][0]['type']=='imm':
        return x['ops'][0]['imm']
    return None

def size_before(call_i, win=10):
    """Return (size, encoding, site_addr) for immediate size before call."""
    for j in range(call_i-1,max(-1,call_i-win),-1):
        x=insns[j]
        if x['mn']=='push' and x['ops'] and x['ops'][0]['type']=='imm':
            return x['ops'][0]['imm'] & 0xFFFFFFFF, 'push_imm8' if x['size']==2 else 'push_imm32', x['addr']
        if x['mn']=='mov' and len(x['ops'])==2 and x['ops'][0]['type']=='reg' and x['ops'][1]['type']=='imm':
            v=x['ops'][1]['imm'] & 0xFFFFFFFF
            if 8 <= v <= 0x10000:
                return v,'mov_reg_imm',x['addr']
        if x['mn'] in ('call','ret','retf'): break
        if x['mn'] in ('add','sub') and x['ops'] and any(o.get('reg')=='esp' for o in x['ops']): break
    return None,None,None

def ctor_after(call_i, limit=12):
    for x in insns[call_i+1:call_i+1+limit]:
        t=call_target(x)
        if t is not None and t not in NEW_THUNKS:
            return t,x['addr']
        if x['mn'] in ('ret','retf','jmp'): return None,None
    return None,None

hits=collections.defaultdict(list)
new_calls=[]
for i,x in enumerate(insns):
    t=call_target(x)
    if t in NEW_THUNKS:
        new_calls.append((x['addr'],t))
        sz,enc,sa=size_before(i)
        ct,ca=ctor_after(i)
        if sz is not None and ct is not None:
            hits[ct].append(dict(call=x['addr'],site=sa,size=sz,enc=enc,ctor_site=ca,kind=NEW_THUNKS[t]))

p("\n=== operator-new call census ===")
p("direct call 0x7C8E17=%d, call 0x7C9442=%d, total=%d" % (
    sum(1 for a,t in new_calls if t==0x7C8E17),
    sum(1 for a,t in new_calls if t==0x7C9442),len(new_calls)))
p("allocation sites with immediate size and following ctor call=%d" % sum(len(v) for v in hits.values()))

p("\n=== target allocation sites (full) ===")
for ct,nm in TARGETS:
    hs=hits.get(ct,[])
    sizes=sorted(set(h['size'] for h in hs))
    if hs:
        state='INDEPENDENT_ALLOC_SITES'
    else:
        state='NOT_FOUND'
    p("%-30s ctor=%08X state=%s sites=%d sizes=%s" % (nm,ct,state,len(hs),[hex(s) for s in sizes]))
    for h in hs:
        p("  size=%08X enc=%-12s size_site=%08X call=%08X ctor_call=%08X kind=%s" % (
            h['size'],h['enc'],h['site'],h['call'],h['ctor_site'],h['kind']))

p("\n=== RawFile 0x24 direct evidence ===")
for a,t in new_calls:
    i=idx[a]; sz,enc,sa=size_before(i); ct,ca=ctor_after(i)
    if sz==0x24:
        p("size_site=%08X call=%08X enc=%s next_call=%08X" % (sa,a,enc,ct or 0))

p("\n=== RawFile ctor bytes and max field offset ===")
i=idx.get(0x65CA80)
if i is not None:
    for x in insns[i:i+70]:
        if x['mn']=='ret': break
        if any(o['type']=='mem' and o.get('base') in ('eax','ecx','esi','edi','ebx','edx') for o in x['ops']):
            p(fmt_ins(x))

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_S03K2R_alloc_tri_state.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT)+'\n')
print('[written EVIDENCE/E_S03K2R_alloc_tri_state.txt]')
