
from pathlib import Path
import csv,pefile,struct,re
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def rd(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def cstr(va):
 b=rd(va,200); return b.split(b'\0')[0].decode('latin1','replace') if b else '<null>'
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dump(a,n=256,c=160):
 print('=== %08X ==='%a)
 for it in md.disasm(rd(a,n),a,count=c):
  ex=''
  for tok in re.findall(r'0x([0-9a-fA-F]{6,8})',it.op_str):
   s=cstr(int(tok,16))
   if s and len(s)>3: ex+=' ; '+repr(s[:80])
  print('%08X %-20s %-8s %s%s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str,ex))
dump(0x65AA80,0x100,120)
print('=== 5B3A10 ===')
dump(0x5B3A10,0x60,60)
print('=== 5B3910 ===')
dump(0x5B3910,0x60,60)
