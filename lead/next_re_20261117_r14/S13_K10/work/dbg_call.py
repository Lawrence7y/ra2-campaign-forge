
import pefile
from capstone import *
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p); img=pe.OPTIONAL_HEADER.ImageBase; raw=open(p,'rb').read()
def off(va): return pe.get_offset_from_rva(va-img)
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=False
for va in [0x43863B,0x438645,0x43864A,0x4386A2,0x4386AB]:
  for i in md.disasm(raw[off(va):off(va)+16],va):
    print(f"{i.address:08X} {i.bytes.hex():<16} |{i.mnemonic}|{i.op_str}|")
    break
