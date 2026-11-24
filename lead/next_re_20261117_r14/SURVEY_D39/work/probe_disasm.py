import pefile
from capstone import *
from capstone.x86 import *
p=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(p,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
sec=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
va=ib+sec.VirtualAddress; off=sec.PointerToRawData; data=open(p,'rb').read()[off:off+sec.SizeOfRawData]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
for start,n in [(0x438640,0x40),(0x438690,0x40),(0x54e2f0,0x30)]:
 print('\n---',hex(start))
 for i in md.disasm(data[start-va:start-va+n],start):
  print(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str, [(o.type,o.size,(hex(o.imm) if o.type==X86_OP_IMM else (hex(o.mem.base)+'/'+hex(o.mem.index)+'/'+hex(o.mem.disp) if o.type==X86_OP_MEM else ''))) for o in i.operands])
