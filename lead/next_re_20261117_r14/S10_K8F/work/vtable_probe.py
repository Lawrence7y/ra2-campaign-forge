import os,struct,datetime
import pefile
from capstone import *
exe=r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
pe=pefile.PE(exe)
base=pe.OPTIONAL_HEADER.ImageBase
print('BASE',hex(base),'sections',[(s.Name.decode().rstrip('\x00'),hex(base+s.VirtualAddress),hex(s.Misc_VirtualSize)) for s in pe.sections])
def off(va): return pe.get_offset_from_rva(va-base)
def u32(va): return struct.unpack_from('<I',pe.__data__,off(va))[0]
def cs(start,n=128):
 c=Cs(CS_ARCH_X86,CS_MODE_32);c.skipdata=True
 return list(c.disasm(pe.__data__[off(start):off(start)+n],start))
for vt in [0x7E22A4,0x7EB058]:
 print('\nVTABLE',hex(vt),'COL',hex(u32(vt-8)),'RTTI?',hex(u32(u32(vt-8)+0xc)))
 for offs in [0x1e8,0x1ec]:
  dst=u32(vt+offs);print(' slot',hex(offs),'->',hex(dst))
  for ins in cs(dst,80):
   print('  %08X  %-24s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
   if ins.mnemonic in ('ret','jmp') and ins.address>dst+20: break
print('\nBASE WRAPPERS')
for dst in [0x5B35E0,0x5B3570]:
 print('---',hex(dst))
 for ins in cs(dst,160):print('  %08X  %-24s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
