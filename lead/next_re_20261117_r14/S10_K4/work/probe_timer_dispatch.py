
from pathlib import Path
import pefile,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
data=(ROOT/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(str(ROOT/'ra2youli/gamemd.exe'),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def rd(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(a,n,c=100):
 b=rd(a,n); return list(md.disasm(b,a,count=c)) if b else []
def dump(a,e):
 print('=== %08X..%08X ==='%(a,e))
 for it in dis(a,e-a,300): print('%08X %-20s %-8s %s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str))
dump(0x5B3060,0x5B30D9)
dump(0x5B30D9,0x5B3110)
print('=== mission dispatch stubs for 19 targets ===')
for a in [0x5B30EA,0x5B323E,0x5B3172,0x5B330A,0x5B32E8,0x5B31D8,0x5B31B6,0x5B31FA,0x5B321C,0x5B3260,0x5B312E,0x5B3150,0x5B3282,0x5B32C6,0x5B32A4,0x5B33D6,0x5B33F8,0x5B345E,0x5B341A]:
 dump(a,a+0x30)
