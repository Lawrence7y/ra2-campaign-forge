import pefile
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(r'D:\Project\ra2-campaign-forge'); EXE=R/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def at(va,n):
 for a,b,p,r in secs:
  if a<=va<b:
   d=va-a
   if d+n<=r:return data[p+d:p+d+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for va,sz in [(0x480110,109),(0x483710,112),(0x4FDDF0,261),(0x485390,199)]:
 print('\nFUNC',hex(va),sz)
 for i in md.disasm(at(va,sz),va): print(f'{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}')
