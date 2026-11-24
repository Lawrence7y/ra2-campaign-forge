
from pathlib import Path
import pefile,struct,re,json
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData,s.Name.rstrip(b'\0').decode('latin1')))
def off(va):
 for a,b,r,z,n in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def rd(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
 b=rd(va,4); return struct.unpack('<I',b)[0] if b else None
def cstr(va):
 b=rd(va,200); return b.split(b'\0')[0].decode('latin1') if b else '<null>'
vt=0x7EDCC0
col=u32(vt-4)
td=u32(col+0xC)
name=cstr(td+8)
print('VTABLE=%08X COL=%08X TD=%08X TD_NAME=%r'%(vt,col,td,name))
print('SLOTS 129..156:')
for i in range(129,157):
 e=u32(vt+4*i)
 print('%3d %08X'%(i,e or 0))
print('COL+8 (wrong chain) =',hex(u32(col+8) or 0))
