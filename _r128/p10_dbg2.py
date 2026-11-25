# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
TXT_LO=0x401000; TXT_HI=0x7e1000
raw=rd(TXT_LO,TXT_HI-TXT_LO)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,_s,m,o in md.disasm_lite(raw,TXT_LO)]
hits=[(a,m,o) for a,m,o in ins if m=='mov' and o=='ecx, 0x87f7e8']
print('n=',len(hits))
for a,m,o in hits[:10]:
    off=a-TXT_LO
    print('0x%08x  bytes %s' % (a, raw[off:off+6].hex()))
print('...')
for a,m,o in hits[-5:]:
    off=a-TXT_LO
    print('0x%08x  bytes %s' % (a, raw[off:off+6].hex()))
# raw pattern count
p=bytes.fromhex('b9e8f78700')
c=0; q=0
while True:
    i=raw.find(p,q)
    if i<0: break
    c+=1; q=i+1
print('raw b9 e8f78700 count =', c)
# .byte count
print('.byte ins =', sum(1 for a,m,o in ins if m=='.byte'))
