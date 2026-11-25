# -*- coding: utf-8 -*-
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
TXT_LO=0x401000; TXT_HI=0x7e1000
raw=rd(TXT_LO,TXT_HI-TXT_LO)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,_s,m,o in md.disasm_lite(raw,TXT_LO)]
print('ins', len(ins))
for hx in ('0x87f7e8','0x89a29c','0xb0c110'):
    r=[(a,m,o) for a,m,o in ins if hx in o.lower()]
    print(hx, len(r))
    c=collections.Counter(o for a,m,o in r)
    for o,n in c.most_common(5):
        print('   %5d  %s' % (n,o[:90]))
