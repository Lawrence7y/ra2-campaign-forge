
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
def cstr(va):
 b=rd(va,200); return b.split(b'\0')[0].decode('latin1','replace') if b else '<null>'
print('=== LoadFromINI keys 0x82C280..0x82C300 ===')
for va in range(0x82C280,0x82C320,4):
 print('%08X %r'%(va,cstr(va)))
print('=== raw strings around 0x82C200 ===')
o=off(0x82C200); print(repr(data[o:o+512]))
print('=== strings around mission table 0x816D00-0x816F00 ===')
o=off(0x816D00); print(repr(data[o:o+512]))
print('=== 005B3760-005B3910 all instructions ===')
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for it in md.disasm(rd(0x5B3760,0x1C0),0x5B3760,count=200):
 extra=''
 if it.mnemonic in ('push','mov') and '0x82' in it.op_str:
  m=re.search(r'0x([0-9a-fA-F]+)',it.op_str)
  if m: extra=' ; STR='+repr(cstr(int(m.group(1),16)))
 print('%08X %-20s %-8s %s%s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str,extra))
