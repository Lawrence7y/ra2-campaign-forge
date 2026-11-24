#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build set of internal jcc/jmp targets (function-body labels) via instruction-boundary sweep.
A shared epilogue / internal label is jumped into by jcc(0x70-7F/0F8x) or jmp(E9/EB) from inside
a function -> NOT_FUNC evidence. Distinct from E8 call targets (criterion a)."""
import pickle, struct, capstone
from pathlib import Path
from engine import Bin
ROOT=Path(r'D:\Project\ra2-campaign-forge'); WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
bin_=Bin()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
t=bin_.text; data=bin_.data[t['raw']:t['raw']+t['rawsize']]
jcc_tgt={}; jmp_tgt={}; njcc=0; njmp=0
for ins in md.disasm(data,t['va']):
    if ins.id==0: continue
    b=ins.bytes
    if len(b)==2 and 0x70<=b[0]<=0x7F:           # jo..js rel8
        tgt=ins.address+2+struct.unpack('<b',b[1:2])[0]
        jcc_tgt.setdefault(tgt,[]).append(ins.address); njcc+=1
    elif len(b)==6 and b[0]==0x0F and 0x80<=b[1]<=0x8F:  # jcc rel32
        tgt=ins.address+6+struct.unpack('<i',b[2:6])[0]
        jcc_tgt.setdefault(tgt,[]).append(ins.address); njcc+=1
    elif len(b)==2 and b[0]==0xEB:               # jmp rel8
        tgt=ins.address+2+struct.unpack('<b',b[1:2])[0]
        jmp_tgt.setdefault(tgt,[]).append(ins.address); njmp+=1
    elif len(b)==5 and b[0]==0xE9:               # jmp rel32
        tgt=ins.address+5+struct.unpack('<i',b[1:5])[0]
        jmp_tgt.setdefault(tgt,[]).append(ins.address); njmp+=1
print('jcc insns',njcc,'distinct targets',len(jcc_tgt))
print('jmp insns',njmp,'distinct targets',len(jmp_tgt))
# disputed rows
for va in (0x405AB0,0x4063A0,0x40A600,0x40BDA0,0x40BE10,0x40C1F0,0x402F80,0x407080):
    print(f'{va:08X} jcc={va in jcc_tgt} sites={[hex(x) for x in jcc_tgt.get(va,[])[:3]]} jmp={va in jmp_tgt} sites={[hex(x) for x in jmp_tgt.get(va,[])[:3]]}')
pickle.dump(dict(jcc_tgt=jcc_tgt,jmp_tgt=jmp_tgt),open(WD/'jcc_idx.pkl','wb'))
# distribution over 1669 and first100
addrs=sorted({int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()})
print('pool jcc-target count',sum(1 for a in addrs if a in jcc_tgt),'of',len(addrs))
print('first100 jcc-target',sum(1 for a in addrs[:100] if a in jcc_tgt))
