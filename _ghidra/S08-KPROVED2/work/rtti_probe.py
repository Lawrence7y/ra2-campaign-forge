import struct,pefile
pe=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
base=pe.OPTIONAL_HEADER.ImageBase; buf=open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe','rb').read()
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def u32(va):
 o=off(va); return struct.unpack('<I',buf[o:o+4])[0] if o is not None else None
def cs(va):
 o=off(va); b=buf[o:o+160]; z=b.find(b'\x00'); return b[:z if z>=0 else len(b)].decode('latin1','replace')
for vt in [0x007E6114,0x007E1964,0x007EFF54,0x007F0344,0x007F1094,0x007F3058,0x007EDFB4,0x007E44F4,0x007E4514,0x007E8B38]:
 col=u32(vt-4); td=u32(col+0xC) if col else None
 print(f'vt={vt:08X} col={col:08X} td={td:08X} name={cs(td+8) if td else ""!r} slots0_13=' + ' '.join(f'{u32(vt+4*i):08X}' for i in range(14)))
