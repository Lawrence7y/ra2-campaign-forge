from re_core import *
from capstone.x86 import X86_OP_MEM
for g in [0x8874c0,0x8874c4,0x8874d0,0xa83c80,0xa83c84,0xa83c90]:
 xs=find_bytes(struct.pack('<I',g),'.text')
 print('GLOBAL',hex(g),'xrefs',[hex(x) for x in xs])
 for x in xs:
  if any(a<=x<a+n for a,n in [(0x75cec0,3000),(0x46bbc0,6000)]):
   print(' ', ' | '.join(fmt(i) for i in dis(x-8,40)))
for ctor,n in [(0x75cec0,3000),(0x46bbc0,6000)]:
 print('CTOR',hex(ctor),'writes +0x24')
 for i in dis(ctor,n):
  if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.disp==0x24:
   print(fmt(i))
