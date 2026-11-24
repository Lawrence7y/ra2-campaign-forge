#!/usr/bin/env python3
"""T3 step 2: vtable dumps with bounds + ctor/dtor discovery via vtable-address immediates."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

def is_col(addr):
    td=u32(addr+0xC)
    if td is None: return False
    nm=read(td+8,8)
    return nm.startswith(b'.?AV')

vfts={}  # start -> COL
for (sec,va,vs,pr,rs,ch) in sections():
    if sec not in ('.rdata','.data'): continue
    blob=read(va,vs)
    for i in range(0,len(blob)-3,4):
        v=struct.unpack_from('<I',blob,i)[0]
        if 0x7E0000 <= v <= 0x830000 and is_col(v):
            vfts[va+i+4]=v
starts=sorted(vfts)
p(f"Total vtable starts found: {len(starts)}")
p("\n=== target vtable dumps (bounded by next vtable start) ===")
targets={'CCFileClass':0x7E16B0,'CDFileClass':0x7E1668,'BufferIOFileClass':0x7E3A2C,
         'RawFileClass':0x7F0904,'MixFileClass':0x7EDF50}
for cls,vft in targets.items():
    col=vfts.get(vft)
    nxt=next((s for s in starts if s>vft), vft+0x200)
    ns=min((nxt-vft)//4, 64)
    p(f"\n--- {cls}: vft={vft:08X} COL={(col or 0):08X} next_start={nxt:08X} slots<={ns} ---")
    for i in range(ns):
        f=u32(vft+4*i)
        if f is None: break
        sec=sec_of(f) or '?'
        fb=read(f,4).hex()
        p(f"    slot[{i:2d}] +0x{i*4:03X}: {f:08X} ({sec}) first={fb}")

p("\n=== functions that write target vft address (ctor/dtor candidates) ===")
from capstone.x86 import X86_OP_IMM, X86_INS_INVALID
text_va=0x401000; text=read(text_va,0x3DF38D)
for cls,vft in [('CCFileClass',0x7E16B0),('CDFileClass',0x7E1668),('BufferIOFileClass',0x7E3A2C),('RawFileClass',0x7F0904),('MixFileClass',0x7EDF50)]:
    hits=set()
    for ins in md.disasm(text, text_va):
        if ins.id!=X86_INS_INVALID:
         for op in ins.operands:
            if op.type==X86_OP_IMM and op.imm==vft:
                hits.add(ins.address)
    p(f"  {cls} vft={vft:08X}: immediate hits = {[hex(a) for a in sorted(hits)]}")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T3_vtables.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T3_vtables.txt]")
