# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
b=rd(0x7e1940, 0x60)
for i in range(0,0x60,16):
    va=0x7e1940+i
    print('0x%08x  %s   %s' % (va, b[i:i+16].hex(' '),
        ' '.join('%08x'%u32(va+j) for j in range(0,16,4))))
print()
for vt in (0x7e1954,0x7e195c,0x7e1964):
    c=col_of(vt)
    print('vt 0x%08x  COL@0x%08x -> %s' % (vt, u32(vt-4), c['type_desc'] if c else None))
print()
print('COL 0x7fa9b8:', {k:c_ for k,c_ in (col_of(0x7e195c) or {}).items() if k in ('signature',)})
for col in (0x7fa9b8, 0x7fab38):
    td=u32(col+12); chd=u32(col+16)
    print('COL 0x%08x sig=%s td=0x%08x(%s) chd=0x%08x n=%s arr=%s'
          % (col, u32(col), td, cstr(td+8,120) if td else None, chd,
             u32(chd+8) if chd else None, hex(u32(chd+12)) if chd else None))
print()
print('--- 0x6d1770 ---')
code=rd(0x6d1770,64)
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for a,sz,m,o in md.disasm_lite(code,0x6d1770):
    print('  0x%08x  %-20s %s %s'%(a,code[a-0x6d1770:a-0x6d1770+sz].hex(),m,o))
