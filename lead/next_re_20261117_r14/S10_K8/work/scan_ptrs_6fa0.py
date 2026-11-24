import struct,pefile
pe=pefile.PE(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe');base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(v):return pe.get_offset_from_rva(v-base)
for t in [0x6b6ea0,0x6b6c90,0x6b6fa0,0x6b7010,0x6b7f10]:
 loc=[]
 for sec in pe.sections:
  o=sec.PointerToRawData;n=sec.SizeOfRawData
  pat=struct.pack('<I',t)
  p=o
  while True:
   p=d.find(pat,p,o+n)
   if p<0:break
   loc.append(base+sec.VirtualAddress+(p-o));p+=1
 print(hex(t),'RAW pointer refs',len(loc),[hex(x) for x in loc[:50]])
