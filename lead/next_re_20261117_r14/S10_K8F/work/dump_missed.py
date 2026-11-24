import struct,pefile
from capstone import *
exe=r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
pe=pefile.PE(exe);base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(va):return pe.get_offset_from_rva(va-base)
cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.skipdata=True
for a in [0x004DFB70,0x004DFCB0,0x004DFE00,0x004D82B0,0x006B6EA0,0x006B6FA0,0x006B6C90,0x006B7F10]:
 print('\n===',hex(a),'===')
 for ins in cs.disasm(d[off(a):off(a)+256],a):
  print('  %08X  %-24s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
  if ins.mnemonic=='ret' and ins.address>a+20:break
