
import sys,json
from capstone import *
secs=json.load(open(sys.argv[1])); exe=open(sys.argv[2],'rb').read()
def off(va):
 rva=va-0x400000
 for s in secs:
  if s['va']<=rva<s['va']+max(s['vs'],s['rs']): return s['raw']+rva-s['va']
md=Cs(CS_ARCH_X86,CS_MODE_32)
for a in [0x65E660,0x65EAB0]:
 o=off(a); print('=== 0x%X ==='%a)
 n=0
 for i in md.disasm(exe[o:o+900],a):
  print('0x%X +0x%X: %s %s'%(i.address,i.address-a,i.mnemonic,i.op_str)); n+=1
  if i.mnemonic=='ret' and n>20: break
