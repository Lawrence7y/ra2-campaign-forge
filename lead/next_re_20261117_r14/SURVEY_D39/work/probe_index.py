import pefile
from capstone import *
p=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(p,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
s=[x for x in pe.sections if x.Name.rstrip(b'\0')==b'.text'][0]
va=ib+s.VirtualAddress;d=open(p,'rb').read()[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
for i in md.disasm(d[0x4386ab-va:0x4386ab-va+6],0x4386ab):
 o=i.operands[0]
 print(hex(i.address),i.mnemonic,i.op_str,'op.index=',getattr(o,'index','NOATTR'),'mem.index=',o.mem.index,'mem.base=',o.mem.base,'disp=',o.mem.disp)
