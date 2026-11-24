import pefile,struct
from capstone import *
pe=pefile.PE(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe');base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(v):return pe.get_offset_from_rva(v-base)
cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.skipdata=True
for a,n,stop in [(0x4dfb70,0x120,0x4dfc67),(0x4dfcb0,0x120,0x4dfdba),(0x4dfe00,0x120,0x4dff00)]:
 print('\nTAIL',hex(a))
 for ins in cs.disasm(d[off(stop):off(a+n)],stop):
  print('  %08X %-20s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
  if ins.mnemonic=='ret' and ins.address>stop+8:break
