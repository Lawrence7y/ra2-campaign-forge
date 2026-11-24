
# -*- coding: utf-8 -*-
import json,struct,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_IMM
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
blob=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
SEC={}
for s in pe.sections: SEC[s.Name.rstrip(b'\x00').decode('latin1')]=(s.VirtualAddress+base,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData)
TVA,Tvs,TPR,TRS=SEC['.text']; TL=TVA; text=blob[TPR:TPR+TRS][:Tvs]
rows=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\rows.json'))
interest={r['entry']:r['hex'] for r in rows}
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
imm=[]; tail=[]
for ins in md.disasm(text,TL):
    if ins.id==0: continue
    mn=ins.mnemonic
    if mn=='call': continue
    if mn=='jmp' and len(ins.operands)==1 and ins.operands[0].type==X86_OP_IMM:
        if ins.operands[0].imm in interest: tail.append((ins.address,ins.operands[0].imm))
        continue
    if mn.startswith('j'): continue
    for op in ins.operands:
        if op.type==X86_OP_IMM and op.imm in interest:
            imm.append((ins.address,ins.operands[0].imm,mn+' '+ins.op_str))
print('true immediate refs (push/mov imm) to S03 entries:',len(imm), imm[:10])
print('tail-jmp refs:',len(tail))
from collections import defaultdict
byE=defaultdict(list)
for s,e,t in imm: byE[e].append(('%08X'%s,t))
json.dump({k:v for k,v in byE.items()},open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\imm_true.json','w'),indent=1)
tailset={e for s,e in tail}
print('entries reachable only via tail-jmp (no E8):',[interest[e] for e in tailset if not rows[[r['entry'] for r in rows].index(e)]['n_direct']])
