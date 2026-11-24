
from pathlib import Path
import pefile,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for s in pe.sections:
 if not (s.Characteristics & 0x20000000): continue
 a=IB+s.VirtualAddress; z=max(s.Misc_VirtualSize,s.SizeOfRawData); r=s.PointerToRawData
 for it in md.disasm(data[r:r+z],a):
  if '816cac' in it.op_str.lower() or '5b34e8' in it.op_str.lower():
   print('%08X %-20s %-8s %s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str))
