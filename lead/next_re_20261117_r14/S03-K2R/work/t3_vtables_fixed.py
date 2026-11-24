#!/usr/bin/env python3
"""T3: vtable dumps with bounds (fixed: no operand access on skipdata insns)."""
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
    return read(td+8,4)==b'.?AV'

vfts={}
for (sec,va,vs,pr,rs,ch) in sections():
    if sec not in ('.rdata','.data'): continue
    blob=read(va,vs)
    for i in range(0,len(blob)-3,4):
        v=struct.unpack_from('<I',blob,i)[0]
        if 0x7E0000<=v<=0x830000 and is_col(v):
            vfts[va+i+4]=v
starts=sorted(vfts)
p(f"Total vtable starts: {len(starts)}")
for cls,vft in [('CCFileClass',0x7E16B0),('CDFileClass',0x7E1668),
                ('BufferIOFileClass',0x7E3A2C),('RawFileClass',0x7F0904),
                ('MixFileClass',0x7EDF50)]:
    col=vfts.get(vft)
    nxt=next((s for s in starts if s>vft),vft+0x200)
    ns=min((nxt-vft)//4,20)
    p(f"\n--- {cls} vft={vft:08X} COL={(col or 0):08X} next={nxt:08X} ---")
    for i in range(ns):
        f=u32(vft+4*i)
        if f is None: break
        p(f"  slot[{i:2d}] {f:08X} ({sec_of(f) or '?'}) first={read(f,4).hex()}")
with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T3_vtables.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T3_vtables.txt]")
