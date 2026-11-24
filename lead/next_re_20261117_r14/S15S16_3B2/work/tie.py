# -*- coding: utf-8 -*-
"""
Tie live dispatch sites to the 7 hit vtables.
Approach: 
  1. find all "call [reg+0x14|0x18]" sites with a following test of al/eax (return consumed)
  2. find all sites in .text that write one of the 7 vtable immediates (ctor writes)
  3. map every instruction to its enclosing atlas function; report functions that
     contain BOTH a ctor write and a slot dispatch (self-contained witness), and
     also functions that contain a slot dispatch followed by a return test.
"""
import json, os, struct, pefile, csv
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
WORK = os.path.join(BASE, r"lead\next_re_20261117_r14\S15S16_3B2\work")
ATLAS = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")

def norm(e):
    e=e.strip().upper(); return e[2:] if e.startswith('0X') else e
atlas={}
with open(ATLAS,encoding='utf-8') as f:
    r=csv.reader(f,delimiter='\t'); next(r)
    for row in r:
        if row and row[0].strip():
            try: atlas[int(row[0],16)]=int(row[1])
            except: pass
fn_starts=sorted(atlas)
import bisect
def enclosing(va):
    i=bisect.bisect_right(fn_starts,va)-1
    if i>=0:
        st=fn_starts[i]; sz=atlas.get(st,0)
        if va < st+sz: return st
    return None

pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase
sections=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1'); va=IB+s.VirtualAddress; sz=max(s.Misc_VirtualSize,s.SizeOfRawData)
    sections.append((nm,va,sz,s.get_data()[:sz]))
text=next(s for s in sections if s[0]=='.text'); TVA,TDAT=text[1],text[3]

wit=json.load(open(os.path.join(WORK,'witness.json'),encoding='utf-8'))
vtables={}
for w in wit:
    for sl in w['slots']:
        if sl['vtable_base']:
            vtables[int(sl['vtable_base'],16)]={'class':sl['rtti_name'],'entry':w['entry'],'slot_off':sl['slot_off']}

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

# collect dispatch sites (call [reg+disp8] with 0x14/0x18) that are followed by a test of eax/al
dispatch=[]
for off in range(0,len(TDAT)-8):
    if TDAT[off]!=0xFF: continue
    b1=TDAT[off+1]
    if (b1>>6)!=1 or ((b1>>3)&7)!=2: continue
    disp=struct.unpack_from('<b',TDAT,off+2)[0]&0xFF
    if disp not in (0x14,0x18): continue
    site=TVA+off
    # disassemble forward 8 bytes from site to see next insn(s)
    nxt=list(md.disasm(TDAT[off:off+12],site))
    consumed=False
    for ins in nxt[1:4]:
        if ins.id in (X86_INS_TEST,X86_INS_CMP):
            consumed=True; break
    dispatch.append({'site':site,'off':disp,'consumed':consumed,
                     'fn':enclosing(site)})

# collect ctor writes of the 7 vtables
ctor_writes=[]
for vb,info in vtables.items():
    needle=struct.pack('<I',vb)
    off=0
    while True:
        i=TDAT.find(needle,off)
        if i<0: break
        va=TVA+i
        # check it's likely mov [..],imm (C7 /0) not B8+r
        ctor_writes.append({'va':va,'vtable':vb,'class':info['class'],'fn':enclosing(va)})
        off=i+1

# functions with both ctor write and dispatch
ctor_fns={c['fn'] for c in ctor_writes if c['fn']}
disp_fns={}
for d in dispatch:
    if d['fn']: disp_fns.setdefault(d['fn'],[]).append(d)
both=sorted(ctor_fns & set(disp_fns))

out=[]
out.append(f"dispatch sites total={len(dispatch)} with_return_test={sum(1 for d in dispatch if d['consumed'])}")
out.append(f"ctor-write sites={len(ctor_writes)} in {len(ctor_fns)} functions")
out.append(f"functions with BOTH ctor write and slot dispatch: {len(both)}")
for fn in both:
    cws=[c for c in ctor_writes if c['fn']==fn]
    ds=disp_fns[fn]
    out.append(f"\nFN {fn:08X} (atlas size={atlas.get(fn)})")
    for c in cws[:6]:
        out.append(f"   ctor write {c['va']:08X} vtable={c['vtable']:08X} {c['class']}")
    for d in ds[:12]:
        out.append(f"   dispatch {d['site']:08X} off=0x{d['off']:X} consumed={d['consumed']}")

# Also: for each hit entry, find the closest dispatch site that has a return test
out.append(f"\n\n=== per-entry nearest consumed dispatch (slot matches) ===")
for w in wit:
    out.append(f"\n{w['entry']} {w['subsystem']} {w['name']}")
    for sl in w['slots']:
        if not sl['vtable_base']: continue
        so=sl['slot_off']
        cands=[d for d in dispatch if d['off']==so and d['consumed']]
        out.append(f"  class={sl['rtti_name']} slot_off=0x{so:X} consumed-dispatch-count={len(cands)}")
        for d in cands[:4]:
            out.append(f"    @{d['site']:08X} fn={('%08X'%d['fn']) if d['fn'] else 'OUT'}")

open(os.path.join(WORK,'tie.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:60]))
