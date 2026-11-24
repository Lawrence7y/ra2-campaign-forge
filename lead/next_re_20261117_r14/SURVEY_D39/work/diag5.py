import pefile
from pathlib import Path
p=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe';raw=Path(p).read_bytes();pe=pefile.PE(data=raw,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
 secs.append((ib+s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData))
def u32(v):
 v&=0xffffffff
 for va,vs,rs,ptr in secs:
  if va<=v<va+max(vs,rs):
   o=ptr+v-va
   if 0<=o<ptr+rs:return int.from_bytes(raw[o:o+4],'little')
 return None
def cs(v,n=100):
 for va,vs,rs,ptr in secs:
  if va<=v<va+max(vs,rs):
   o=ptr+v-va
   if 0<=o<ptr+rs:
    b=raw[o:o+n];z=b.find(b'\0');b=b[:z] if z>=0 else b
    try:return b.decode('ascii')
    except:return ''
 return ''
for vt in [0x7e17d8,0x7e17ec,0x7e1e38,0x7e43d4,0x7e4684,0x7e7ea4]:
 col=u32(vt-4);td=u32(col+0xC) if col else None;print(hex(vt),'vt-4',hex(u32(vt-4) or 0),'col',hex(col or 0),'td',hex(td or 0),'name',repr(cs(td+8) if td else ''))
