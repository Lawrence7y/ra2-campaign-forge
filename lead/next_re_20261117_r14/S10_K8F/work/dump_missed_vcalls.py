import pefile
from capstone import *
pe=pefile.PE(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe');base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(v):return pe.get_offset_from_rva(v-base)
cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.skipdata=True
for st,en in [(0x4dfc83,0x4dfcc0),(0x4dfdcb,0x4dfe00)]:
 print('\nWINDOW',hex(st),hex(en))
 for ins in cs.disasm(d[off(st):off(en)],st):
  print('  %08X %-24s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
