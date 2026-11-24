import struct,sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K5\work')
from re_lib import *
TARGET=0x5B3A10
print('=== DIRECT CALL XREFS TO 005B3A10 ===')
for s in PE.sections:
 if not (s.Characteristics & 0x20): continue
 base=PE.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
 n=min(s.SizeOfRawData,s.Misc_VirtualSize or s.SizeOfRawData)
 data=read(base,n)
 for j in range(len(data)-5):
  if data[j]!=0xE8: continue
  rel=struct.unpack_from('<i',data,j+1)[0]
  va=base+j
  if va+5+rel==TARGET:
   print('call@0x%08X'%va)
   print(fmt_block(max(0,va-80),count=60,stop_ret=True,max_bytes=512))
for a in [0x5B3650,0x5B36B0,0x5B3700,0x5B3760,0x5B3910]:
 print('\n===== 0x%08X ====='%a)
 print(fmt_block(a,count=180,stop_ret=True,max_bytes=8192))
