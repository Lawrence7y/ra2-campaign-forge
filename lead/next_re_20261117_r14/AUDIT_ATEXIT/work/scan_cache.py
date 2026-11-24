
# -*- coding: utf-8 -*-
"""AUDIT-ATEXIT step1: one linear disasm pass of .text -> compact pickle cache."""
import pefile, capstone, pickle, sys, os
from capstone import *
from capstone.x86 import *
from array import array
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=os.path.dirname(os.path.abspath(__file__))
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
blob=open(EXE,'rb').read()
secs=[dict(name=s.Name.decode().rstrip('\x00'),va=IB+s.VirtualAddress,
           vsize=s.Misc_VirtualSize,rawsize=s.SizeOfRawData,rawptr=s.PointerToRawData) for s in pe.sections]
TEXT=next(s for s in secs if s['name']=='.text')
TEXT_LO,TEXT_HI=TEXT['va'],TEXT['va']+TEXT['vsize']
rawptr=TEXT['rawptr']
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
addrs=array('I'); sizes=array('B'); flags=array('B')
F_RET=1;F_PUSH=2;F_CALLI=4;F_JMPI=8
pushval={};calltgt={};jmptgt={};store_imm=[];store_reg={};movreg={};immref={}
for ins in md.disasm(blob[rawptr:rawptr+TEXT['vsize']], TEXT_LO):
    if ins.id==0: continue
    a=ins.address;sz=ins.size;mn=ins.mnemonic;ops=ins.operands
    fl=0
    if mn.startswith('ret'): fl|=F_RET
    if len(ops)>=1 and ops[0].type==X86_OP_IMM and mn in ('call','jmp') and TEXT_LO<=ops[0].imm<TEXT_HI:
        if mn=='call': calltgt[a]=ops[0].imm; fl|=F_CALLI
        else: jmptgt[a]=ops[0].imm; fl|=F_JMPI
    for o in ops:
        if o.type==X86_OP_IMM and TEXT_LO<=o.imm<TEXT_HI:
            immref.setdefault(o.imm,[]).append(a)
    if mn=='push' and ops and ops[0].type==X86_OP_IMM and TEXT_LO<=ops[0].imm<TEXT_HI:
        pushval[a]=ops[0].imm; fl|=F_PUSH
    if len(ops)==2 and mn.startswith('mov'):
        o0,o1=ops
        if o0.type==X86_OP_MEM and o1.type==X86_OP_IMM and 0x400000<=o1.imm<0xC00000:
            absl = (o0.mem.base==0 and o0.mem.index==0)
            store_imm.append((a,o1.imm,'abs' if absl else 'reg', o0.mem.disp if absl else None))
        elif o0.type==X86_OP_MEM and o1.type==X86_OP_REG and o1.size==4:
            store_reg.setdefault(a,[]).append(o1.reg)
        elif o0.type==X86_OP_REG and o0.size==4 and o1.type==X86_OP_IMM and 0x400000<=o1.imm<0xC00000:
            movreg[a]=(o0.reg,o1.imm)
    addrs.append(a);sizes.append(sz);flags.append(fl)
print('insns',len(addrs),'push',len(pushval),'call',len(calltgt),'jmp',len(jmptgt),
      'store_imm',len(store_imm),'store_reg',len(store_reg),'movreg',len(movreg),'immref',len(immref),file=sys.stderr)
pickle.dump(dict(secs=secs,text=[TEXT_LO,TEXT_HI],addrs=addrs,sizes=sizes,flags=flags,
                 pushval=pushval,calltgt=calltgt,jmptgt=jmptgt,store_imm=store_imm,
                 store_reg=store_reg,movreg=movreg,immref=immref), open(os.path.join(OUT,'insns.pkl'),'wb'), protocol=4)
print('WROTE insns.pkl',file=sys.stderr)
