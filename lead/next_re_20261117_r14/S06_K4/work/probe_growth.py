import pefile,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(r'D:\Project\ra2-campaign-forge'); data=(R/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(str(R/'ra2youli/gamemd.exe'),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def at(va,n):
 for a,b,p,r in secs:
  if a<=va<b:
   d=va-a
   if d+n<=r:return data[p+d:p+d+n]
def off(va):
 for a,b,p,r in secs:
  if a<=va<b:return p+va-a
def q(va): return struct.unpack_from('<d',data,off(va))[0]
print('const 0x7E3810 double',q(0x7E3810),'bytes',at(0x7E3810,8).hex())
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for va,sz in [(0x487190,300),(0x5FDD20,160)]:
 print('\nFUNC',hex(va))
 for i in md.disasm(at(va,sz),va): print(f'{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}')
