
import sys, pefile
from capstone import *
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p); img=pe.OPTIONAL_HEADER.ImageBase; raw=open(p,'rb').read()
def off(va):return pe.get_offset_from_rva(va-img)
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=False
for s in sys.argv[1:]:
 va=int(s,16);print("===",s,"===")
 for i in md.disasm(raw[off(va):off(va)+80],va):
  print(f" {i.address:08X} {i.bytes.hex():<16} {i.mnemonic} {i.op_str}")
