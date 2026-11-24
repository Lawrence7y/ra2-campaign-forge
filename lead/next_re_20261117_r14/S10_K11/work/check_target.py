
import os, hashlib, capstone, pefile
p=r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
print('exists', os.path.exists(p), 'size', os.path.getsize(p) if os.path.exists(p) else None)
if os.path.exists(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20), b''): h.update(b)
 print('sha256', h.hexdigest())
print('capstone', capstone.__version__, 'pefile', pefile.__version__)
pe=pefile.PE(p)
print('ImageBase', hex(pe.OPTIONAL_HEADER.ImageBase), 'Entry', hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
for va in (0x004DFCB0,0x004DFE00):
 o=pe.get_offset_from_rva(va-pe.OPTIONAL_HEADER.ImageBase)
 print(hex(va), 'rva', hex(va-pe.OPTIONAL_HEADER.ImageBase), 'off', hex(o))
