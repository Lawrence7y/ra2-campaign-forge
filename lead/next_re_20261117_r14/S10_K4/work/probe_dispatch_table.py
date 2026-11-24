
from pathlib import Path
import pefile,struct
ROOT=Path(r'D:\Project\ra2-campaign-forge')
data=(ROOT/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(str(ROOT/'ra2youli/gamemd.exe'),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def u32(va):
 o=off(va); return struct.unpack_from('<I',data,o)[0] if o is not None else None
def cstr(va):
 o=off(va); return data[o:data.index(b'\0',o)].decode('latin1') if o is not None else '<null>'
names=[cstr(u32(0x816CAC+4*i)) for i in range(32)]
table=[u32(0x5B34E8+4*i) for i in range(32)]
for i,(n,a) in enumerate(zip(names,table)):
 print('%2d %-20s %08X'%(i,n,a))
print('groups:')
g={}
for i,a in enumerate(table): g.setdefault(a,[]).append(i)
for a,mids in sorted(g.items(),key=lambda kv:kv[0]): print('%08X %s %s'%(a,mids,','.join(names[m] for m in mids)))
