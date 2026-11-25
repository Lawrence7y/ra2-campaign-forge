# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
def dis(va, n=140, label=''):
    print('=== %s 0x%08x ===' % (label, va))
    code = rd(va, n)
    for a, sz, m, o in md.disasm_lite(code, va):
        print('  0x%08x  %-28s %s %s' % (a, code[a-va:a-va+sz].hex(), m, o))
    print()
dis(0x429360, 150, 'IApplication QI (ApplicationClass)')
dis(0x429270, 110, 'TiberianSunClassFactory slot3 (forwarding QI)')
dis(0x4292cf, 160, 'TSClassFactory QI cont')
