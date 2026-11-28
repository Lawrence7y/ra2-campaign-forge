# -*- coding: utf-8 -*-
"""R209 q0: 速览 6 个目标址的字节与反汇编（小窗口，无 OOM 风险）。"""
import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
for a in (0x4105e0,0x410590,0x410580,0x6d1770,0x410260,0x414290,0x41c670,0x41c680,0x41c690):
    o=P.r2o(a)
    b=P.RAW[o:o+48]
    ins=list(md.disasm(P.RAW[o:o+48],a))
    print('== %08x [%s] %s'%(a,P.where(a),b.hex(' ')))
    for i in ins[:12]:
        print('   %08x %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
