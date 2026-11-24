import pefile
from pathlib import Path
p=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe';raw=Path(p).read_bytes();pe=pefile.PE(data=raw,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
targets={0x0040BBC0,0x0040B640,0x00459FF0,0x004AF610,0x0040EEC0,0x0046B5E0}
for s in pe.sections:
 nm=s.Name.rstrip(b'\0').decode('latin1')
 if nm=='.text':continue
 va=ib+s.VirtualAddress; ptr=s.PointerToRawData; rs=s.SizeOfRawData
 print(nm,hex(va),hex(rs))
 for o in range(ptr,ptr+rs-3,4):
  v=int.from_bytes(raw[o:o+4],'little')
  if v in targets: print(' hit',hex(va+o-ptr),hex(v))
