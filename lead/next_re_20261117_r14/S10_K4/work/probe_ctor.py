
from pathlib import Path
import pefile,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def rd(va,n):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z:
   o=r+va-a
   return data[o:o+n] if o+n<=len(data) else None
 return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for it in md.disasm(rd(0x5B2DA0,0x180),0x5B2DA0,count=120):
 if '7edcc0' in it.op_str.lower() or it.mnemonic in ('ret',):
  print('%08X %-20s %-8s %s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str))
