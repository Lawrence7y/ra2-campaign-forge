# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
a=0x4f68fc; o=P.r2o(a)
for i in md.disasm(P.RAW[o:o+80],a):
    print('  %08x  %-18s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
    if i.mnemonic.startswith('ret'): break
