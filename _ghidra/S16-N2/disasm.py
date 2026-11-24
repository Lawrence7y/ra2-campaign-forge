
import sys,json
from capstone import *
secs=json.load(open(sys.argv[1]))
exe=open(sys.argv[2],'rb').read()
def off(va):
 rva=va-0x400000
 for s in secs:
  if s['va']<=rva<s['va']+max(s['vs'],s['rs']): return s['raw']+rva-s['va']
 raise Exception('unmap')
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
for a in [int(x,16) for x in sys.argv[3:]]:
 o=off(a)
 print('===== 0x%08X fileoff=0x%X ====='%(a,o))
 n=0
 for i in md.disasm(exe[o:o+600],a):
  print('0x%08X +0x%03X: %-8s %s'%(i.address,i.address-a,i.mnemonic,i.op_str)); n+=1
  if i.mnemonic=='ret' or n>=120: break
