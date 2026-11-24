
from pathlib import Path
import pefile,struct,re
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
data=(ROOT/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(str(ROOT/'ra2youli/gamemd.exe'),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
 secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData,s.Name.rstrip(b'\0').decode('latin1')))
def off(va):
 for a,b,r,z,n in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def rd(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
 b=rd(va,4); return None if b is None else struct.unpack('<I',b)[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(a,n=256,c=80):
 b=rd(a,n); return list(md.disasm(b,a,count=c)) if b else []
print('=== 005B3740 GetMissionName-ish ===')
for it in dis(0x5B3740,0x100,90): print('%08X %-20s %s ; %s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str))
print('=== TABLE 0x816CAC 40 ptrs ===')
for i in range(40):
 p=u32(0x816CAC+4*i)
 b=rd(p,80) if p else b''
 s=b.split(b'\0')[0].decode('latin1','replace') if b else '<null>'
 print('%2d ptr=%08X str=%r'%(i,p or 0,s))
print('=== ASCII strings containing mission words ===')
for m in re.finditer(rb'[ -~]{4,}',data):
 s=m.group().decode('latin1')
 if re.search(r'(?i)(mission|harmless|ambush|sabotage|paradrop|spyplane|area guard|defaultmission|capture)',s):
  o=m.start(); va=None
  for a,b,r,z,n in secs:
   if r<=o<r+z: va=a+o-r; break
  print('%08X %r'%(va or 0,s[:180]))
