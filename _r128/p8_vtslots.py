# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va, n=70, label=''):
    print('=== %s 0x%08x ===' % (label, va))
    code = rd(va, n)
    for a, sz, m, o in md.disasm_lite(code, va):
        print('  0x%08x  %-24s %s %s' % (a, code[a-va:a-va+sz].hex(), m, o))
        if m=='ret' or (m=='jmp' and o.startswith('0x')): break
    print()
for va,lab in [(0x429210,'0x7ea564 slot0'),(0x4e8240,'slot1'),(0x4e8250,'slot2'),
               (0x4e8260,'slot4'),(0x4e8270,'slot6')]:
    dis(va, 72, lab)
print('0x7e195c COL:')
c=col_of(0x7e195c)
print(' ', c['type_desc'] if c else None, [(b['name'],b['mdisp']) for b in c['bases']] if c else None)
