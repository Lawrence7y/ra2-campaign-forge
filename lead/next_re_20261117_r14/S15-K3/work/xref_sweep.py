#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full .text sweep for direct call/jmp references to each candidate; map caller to atlas function."""
import sys, csv, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p
from capstone.x86 import X86_OP_IMM

ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
funcs=[]
with open(ATL,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        e=(r['entry'] or '').strip()
        try:
            va=int(e,16); sz=int(r['size'])
            funcs.append((va,sz,e,r['name'] if 'name' in r else ''))
        except: pass
funcs.sort()
starts=[x[0] for x in funcs]
def owner(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and funcs[i][0]<=va<funcs[i][0]+funcs[i][1]:
        return funcs[i]
    return None

CAND = {
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
}

# sweep .text with capstone skipdata, collect call/jmp imm targets that are candidates
sec=None
for s in p._pe.sections:
    if s.Name.decode(errors='replace').rstrip('\x00')=='.text':
        sec=s;break
code=p._pe.__data__[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
base=0x400000+sec.VirtualAddress
refs={c:[] for c in CAND}
for insn in p._md.disasm(code, base):
    if insn.mnemonic in ('call','jmp') and insn.operands and insn.operands[0].type==X86_OP_IMM:
        t=insn.operands[0].imm
        if t in CAND:
            refs[t].append((insn.address, insn.mnemonic, owner(insn.address)))

for c in sorted(CAND):
    print("="*80)
    print(f"0x{c:08X}  xrefs={len(refs[c])}")
    for addr,mn,own in refs[c]:
        ownstr = f"owner={own[2]}[sz={own[1]}]" if own else "owner=NONE(outside atlas)"
        print(f"  {mn:4s} @0x{addr:08X}  {ownstr}")
