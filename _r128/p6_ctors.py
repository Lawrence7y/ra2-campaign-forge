# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va, n=90, label=''):
    print('=== %s 0x%08x ===' % (label, va))
    code = rd(va, n)
    for a, sz, m, o in md.disasm_lite(code, va):
        print('  0x%08x  %s' % (a, ('%s %s'%(m,o))))
    print()
dis(0x40d140, 130, 'site writing 0x87f7e8 <- 0x7e1964')
dis(0x6cf080, 150, 'site writing 0xb0c110 <- 0x7f4108')
dis(0x4291c0, 90, 'site writing 0x89a29c <- 0x7e36d4')
