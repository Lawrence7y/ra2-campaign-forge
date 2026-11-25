# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def dis(va,n=120,lab=''):
    print('=== %s 0x%08x ==='%(lab,va))
    code=rd(va,n)
    for a,sz,m,o in md.disasm_lite(code,va):
        print('  0x%08x  %-22s %s %s'%(a,code[a-va:a-va+sz].hex(),m,o))
    print()
dis(0x429210,80,'0x7ea564 slot0 (native QI)')
print('0x7e36d4 slots:',['0x%08x'%u32(0x7e36d4+4*i) for i in range(8)])
print('0x7e195c slots:',['0x%08x'%u32(0x7e195c+4*i) for i in range(12)])
