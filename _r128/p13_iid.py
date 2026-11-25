# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone, json
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
TXT_LO=0x401000; TXT_HI=0x7e1000
raw=rd(TXT_LO,TXT_HI-TXT_LO)
ins=[(a,m,o) for a,_s,m,o in md.disasm_lite(raw,TXT_LO)]
md.skipdata=True
# 0x7ea6e8 的全部指令级引用
for hx in ('0x7ea6e8',):
    r=[(a,m,o) for a,m,o in ins if hx in o.lower()]
    print(hx, len(r))
    for a,m,o in r: print('   0x%08x  %-8s %s' % (a,m,o))
print()
# 找所有「比较 0x7ea6e8 的 QI 体」= mov edi,0x7ea6e8 后接 repe cmpsd
