# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va, n=120, label=''):
    print('=== %s 0x%08x ===' % (label, va))
    code = rd(va, n)
    for a, sz, m, o in md.disasm_lite(code, va):
        print('  0x%08x  %-24s %s %s' % (a, code[a-va:a-va+sz].hex(), m, o))
    print()
dis(0x4f4240, 200, 'vt 0x7e1964 slot0  (MouseClass QI?)')
dis(0x5bda40, 120, 'ctor called with ecx=0x87f7e8')
