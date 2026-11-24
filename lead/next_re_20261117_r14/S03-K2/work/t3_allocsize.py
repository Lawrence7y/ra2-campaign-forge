#!/usr/bin/env python3
"""T3: find vptr-writing ctors/dtors + allocation sizes for new classes."""
import sys, os, struct, csv
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_INS_INVALID
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())
text_va=0x401000; text=read(text_va,0x3DF38D)
vfts={0x7E3A2C:'BufferIOFileClass',0x7F0904:'RawFileClass',0x7E1668:'CDFileClass'}
p("=== insns writing target vft immediate to [mem] ===")
for v,nm in vfts.items():
    hits=[]
    for ins in md.disasm(text,text_va):
        if ins.id==X86_INS_INVALID: continue
        try:
            ops=ins.operands
            if len(ops)>=2 and ops[0].type==X86_OP_MEM:
                if any(op.type==X86_OP_IMM and op.imm==v for op in ops[1:]):
                    hits.append(ins.address)
        except Exception: pass
    p(f"  {nm} vft={v:08X}: {[hex(a) for a in hits]}")

# For each ctor candidate function, classify ctor vs dtor by presence of operator delete 0x7c8b3d/0x7c93e8
p("\n=== allocation sizes: scan push-imm; call 0x7C8E17 then look for ctor call ===")
# collect all sites 'call 0x7C8E17' with preceding push imm
sites=[]
inslist=list(md.disasm(text,text_va))
for i,ins in enumerate(inslist):
    if ins.id==X86_INS_INVALID: continue
    try:
        if ins.mnemonic=='call' and ins.op_str.strip()=='0x7c8e17':
            # search back up to 4 insns for push imm
            for j in range(i-1,max(-1,i-5),-1):
                pi=inslist[j]
                if pi.id==X86_INS_INVALID: continue
                if pi.mnemonic=='push':
                    try:
                        sz=int(pi.op_str,16)
                        if 0x10<=sz<=0x200:
                            sites.append((ins.address,sz,pi.address))
                            break
                    except Exception: pass
    except Exception: pass
p(f"  allocation sites with push-imm size: {len(sites)}")
# for each known ctor, find which sizes precede calls to it
for ctor,nm in [(0x431B20,'BufferIOFileClass::ctor'),(0x4739F0,'CCFileClass::ctor'),(0x5B3C20,'MixFileClass::ctor')]:
    found=set()
    for sa,sz,pa in sites:
        # look forward 32 bytes from sa for call ctor
        b=read(sa,40)
        for ins in md.disasm(b,sa):
            if ins.id==X86_INS_INVALID: continue
            try:
                if ins.mnemonic=='call' and int(ins.op_str,16)==ctor:
                    found.add(sz); break
            except Exception: pass
    p(f"  {nm}: sizes from new+push = {[hex(x) for x in sorted(found)]}")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T3_allocsize.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T3_allocsize.txt]")
