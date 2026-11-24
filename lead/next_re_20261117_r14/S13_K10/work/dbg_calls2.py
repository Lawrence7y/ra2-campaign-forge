
import pefile,struct
from capstone import *
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p);img=pe.OPTIONAL_HEADER.ImageBase;raw=open(p,'rb').read()
def off(va):return pe.get_offset_from_rva(va-img)
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
tva=img+text.VirtualAddress;tsz=text.SizeOfRawData
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=False
G=0x89C668
buf=raw[off(tva):off(tva)+tsz]
hits=[]
for ins in md.disasm(buf,tva):
 if ins.mnemonic=='call' and 'ptr [edx +' in ins.op_str:
  o=off(ins.address); pre=raw[max(0,o-80):o]
  if b'\xb9'+struct.pack('<I',G) in pre and b'\x8b\x15'+struct.pack('<I',G) in pre:
   hits.append((hex(ins.address),ins.op_str))
print("call [edx+..] with mov ecx,G + mov edx,[G] in prev 80B:",len(hits))
for h in hits[:20]: print(h)
