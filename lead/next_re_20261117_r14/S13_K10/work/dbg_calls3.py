
import pefile,re
from capstone import *
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p);img=pe.OPTIONAL_HEADER.ImageBase;raw=open(p,'rb').read()
def off(va):return pe.get_offset_from_rva(va-img)
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
tva=img+text.VirtualAddress;tsz=text.SizeOfRawData
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=False
# find all call [reg+0xC] preceded by mov edx,[G] where G has C7 05 ... 0x7E17CC
Gtargets={0x89C668:0x7E17CC}
import struct
for i in range(tva,tva+tsz-10):
 o=off(i)
 if raw[o:o+2]==b'\xc7\x05':
  G=struct.unpack_from('<I',raw,o+2)[0];VT=struct.unpack_from('<I',raw,o+6)[0]
  if VT==0x7E17CC: Gtargets[G]=VT
print("G for vt 0x7E17CC:",[hex(g) for g in Gtargets])
buf=raw[off(tva):off(tva)+tsz]
hits=[]
for ins in md.disasm(buf,tva):
 if ins.mnemonic=='call' and ins.op_str=='dword ptr [edx + 0xc]':
  # look back in raw bytes 30 for mov edx,[G]
  o=off(ins.address); pre=raw[max(0,o-30):o]
  for g in Gtargets:
   pat=b'\x8b\x15'+struct.pack('<I',g)
   if pat in pre: hits.append((hex(ins.address),hex(g),pre[-30:].hex()))
print("call [edx+0xC] near vt-global:",len(hits))
for h in hits[:10]: print(h)
