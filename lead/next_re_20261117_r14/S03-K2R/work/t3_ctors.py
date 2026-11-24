#!/usr/bin/env python3
"""T3 step 3: disassemble slot0 ctors + scan allocation sizes (push imm; call 0x7C8E17)."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
from capstone.x86 import X86_OP_IMM, X86_INS_INVALID
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

def dump(start, nbytes, cap=30):
    for ins in dis(start,nbytes,cap):
        p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic:8} {ins.op_str}")

# slot0 of each class = likely ctor (vptr writer)
p("=== slot0 ctor candidates ===")
for cls,fn in [('CDFileClass',0x401950),('BufferIOFileClass',0x432610),('RawFileClass',0x65D3A0),
               ('CCFileClass',0x4019A0),('MixFileClass',0x5B4630)]:
    p(f"\n--- {cls} slot0 {fn:08X} ---")
    dump(fn,0x40,20)

# find all 'call 0x7C8E17' (operator new wrapper) sites, look back for push imm
p("\n=== allocation sites: scan .text for call 0x7C8E17, inspect preceding 3 insns ===")
text_va=0x401000; text=read(text_va,0x3DF38D)
new_sites=[]
for ins in md.disasm(text,text_va):
    if ins.id in (X86_INS_INVALID,0): continue
    try:
        if ins.mnemonic=='call' and ins.op_str.strip()=='0x7c8e17':
            new_sites.append(ins.address)
    except Exception: pass
p(f"total call 0x7C8E17 sites = {len(new_sites)}")

# For each site, disassemble backwards-ish: show 24 bytes before and the call
def ctx(va,n=32):
    start=va-n
    lines=[]
    for ins in dis(start,n+8,20):
        if ins.address<=va:
            lines.append(f"    {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic:8} {ins.op_str}")
        if ins.address>=va+5: break
    return lines

# focus on sites whose following call target is one of the ctors
ctors={'CDFileClass':0x401950,'BufferIOFileClass':0x431B20,'RawFileClass':0x65D3A0,
       'CCFileClass':0x4739F0,'MixFileClass':0x5B3C20}
# find 'call ctor' sites and look back for push imm / call new
for cls,ctor in ctors.items():
    p(f"\n--- {cls} ctor {ctor:08X}: call sites with preceding push-imm ---")
    sites=[]
    for ins in md.disasm(text,text_va):
        if ins.id in (X86_INS_INVALID,0): continue
        try:
            if ins.mnemonic=='call' and ins.op_str.strip()==hex(ctor)[2:].lower().rjust(0,'0'):
                sites.append(ins.address)
        except Exception: pass
    # Note op_str for call rel32 is like '0x401950'
    sites=[]
    for ins in md.disasm(text,text_va):
        if ins.id in (X86_INS_INVALID,0): continue
        try:
            if ins.mnemonic=='call':
                tgt=int(ins.op_str,16)
                if tgt==ctor: sites.append(ins.address)
        except Exception: pass
    p(f"  call sites = {len(sites)}: {[hex(a) for a in sites[:20]]}")
    for sa in sites[:6]:
        for l in ctx(sa,40): p(l)

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T3_ctors_alloc.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T3_ctors_alloc.txt]")
