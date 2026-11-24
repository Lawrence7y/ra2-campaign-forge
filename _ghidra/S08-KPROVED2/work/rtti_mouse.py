import struct,pefile
pe=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'); base=pe.OPTIONAL_HEADER.ImageBase; buf=open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe','rb').read()
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def u32(va):
 o=off(va); return struct.unpack('<I',buf[o:o+4])[0] if o is not None else None
for vt,name in [(0x007E1964,'MouseClass')]:
 print(name, ' '.join(f's{i}={u32(vt+4*i):08X}' for i in range(40,47)))
 print('vt-4',f'{u32(vt-4):08X}','col+0xC',f'{u32(u32(vt-4)+0xC):08X}')
