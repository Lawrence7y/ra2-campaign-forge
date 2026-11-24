import struct,pefile,os
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\EVIDENCE\VT_SLOT_MAP.tsv'
pe=pefile.PE(EXE); base=pe.OPTIONAL_HEADER.ImageBase; buf=open(EXE,'rb').read()
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def u32(va):
 o=off(va); return struct.unpack('<I',buf[o:o+4])[0] if o is not None else None
with open(OUT,'w',encoding='utf-8') as f:
 f.write('vt\tslot\tslot_va\tvalue\n')
 for vt,n in [(0x007E44F4,14),(0x007E4514,7),(0x007E8B38,25),(0x007E1964,55)]:
  for i in range(n): f.write(f'{vt:08X}\t{i}\t{vt+4*i:08X}\t{u32(vt+4*i):08X}\n')
print('wrote',OUT)
