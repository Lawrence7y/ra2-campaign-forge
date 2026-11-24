#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare strict predecessor variants to find a NON-circular within-pool discriminator."""
import pickle, capstone, random
from collections import Counter
from engine import Bin
ROOT=__import__('pathlib').Path(r'D:\Project\ra2-campaign-forge')
WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
bin_=Bin()
HARD={'ret','retf','int3','hlt','ud2'}       # genuine function end
JMP={'jmp'}                                   # may be internal tail
B0HARD={0xC3,0xC2,0xCC,0xF4,0xCB,0xCA}
B0JMP={0xEB,0xE9,0xEA}

def boundary_class(va):
    npad=0
    while npad<16 and bin_.u8(va-1-npad) in (0x90,0xCC): npad+=1
    pad_end=va-npad
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False; md.skipdata=True
    for start in range(pad_end-12,pad_end):
        if start<bin_.text['va']: continue
        seg=bin_.read(start,pad_end-start+4)
        if not seg: continue
        for insn in md.disasm(seg,start):
            if insn.id==0: continue
            if insn.address+insn.size==pad_end:
                m=insn.mnemonic
                if m in HARD or insn.bytes[0] in B0HARD: return ('hard',f'{m}@{start:X} pad{npad}')
                if m in JMP or insn.bytes[0] in B0JMP: return ('jmp',f'{m}@{start:X} pad{npad}')
                return ('other',f'{m}@{start:X} pad{npad}')
            if insn.address>=pad_end: break
    return ('none',f'pad{npad}')

addrs=sorted({int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()})
cls=[boundary_class(a) for a in addrs]
print('FULL POOL 1669 boundary class:', dict(Counter(c for c,_ in cls)))

for name,idxs in [('first100',range(100)),('pool_rand100',random.Random(20261119).sample(range(1669),100))]:
    sub=[cls[i][0] for i in idxs]
    print(name, dict(Counter(sub)),
          'hard%=', round(100*sum(1 for x in sub if x=='hard')/len(sub),1),
          'hard_or_jmp%=', round(100*sum(1 for x in sub if x in ('hard','jmp'))/len(sub),1))

# global
t=bin_.text; lo=(t['va']+15)//16*16; hi=(t['va']+t['vsize'])//16*16; nal=(hi-lo)//16
g=[lo+16*i for i in random.Random(20261119).sample(range(nal),100)]
gc=[boundary_class(a)[0] for a in g]
print('global_rand100',dict(Counter(gc)),'hard%=',round(100*sum(1 for x in gc if x=='hard'),1))
