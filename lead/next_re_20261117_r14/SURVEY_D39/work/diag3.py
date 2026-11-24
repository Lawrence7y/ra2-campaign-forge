import pefile
from pathlib import Path
p=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe';raw=Path(p).read_bytes();pe=pefile.PE(data=raw,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
 nm=s.Name.rstrip(b'\0').decode('latin1');secs.append((nm,ib+s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData))
def va2off(v):
 v&=0xffffffff
 for nm,va,vs,rs,ptr in secs:
  if va<=v<va+rs:return ptr+v-va
 return None
def u32(v):
 o=va2off(v)
 return None if o is None else int.from_bytes(raw[o:o+4],'little')
def cstr(v,n=100):
 o=va2off(v)
 if o is None:return ''
 b=raw[o:o+n];z=b.find(b'\0');b=b[:z] if z>=0 else b
 try:return b.decode('ascii')
 except:return ''
for vt in [0x7F73B8,0x7EB054,0x7E3D10,0x7E22A4]:
 col=u32(vt-4);td=u32(col+0xC) if col else None;name=cstr(td+8) if td else ''
 print(hex(vt),'col',hex(col) if col else None,'td',hex(td) if td else None,'name',repr(name),'dwordvt',hex(u32(vt) or 0))
print('sections')
for x in secs:print(x)
