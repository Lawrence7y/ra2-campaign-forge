import pefile
from capstone import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE); base=pe.OPTIONAL_HEADER.ImageBase; buf=open(EXE,'rb').read()
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def read(va,n):
 o=off(va); return b'' if o is None else buf[o:o+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
for site in [0x00457BFD,0x0045AB06,0x0045AC96,0x004D088F,0x0040D295]:
 start=site-0x90
 ins=list(md.disasm(read(start,0x140),start,0x140))
 print(f'\n===== SITE {site:08X} =====')
 for i in ins:
  mark='>>' if i.address==site else '  '
  print(f'{mark} {i.address:08X}  {i.bytes.hex():<16}  {i.mnemonic:<8} {i.op_str}')
