import pathlib,struct,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM
pe=pefile.PE(str(pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")),fast_load=False);ib=pe.OPTIONAL_HEADER.ImageBase;data=pe.__data__
def ro(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u(va):
 o=ro(va-ib);return None if o is None else struct.unpack_from("<I",data,o)[0]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
text=next(s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text')
ins=list(md.disasm(data[text.PointerToRawData:text.PointerToRawData+min(text.SizeOfRawSize if hasattr(text,'SizeOfRawSize') else text.SizeOfRawData,text.Misc_VirtualSize)],ib+text.VirtualAddress))
# simpler raw byte E8 direct calls to candidate entries
for e in [0x468670,0x629fd0,0x62a260]:
 raw=[]
 for j,x in enumerate(ins):
  if x.mnemonic=='call' and x.operands and x.operands[0].type==X86_OP_IMM and x.operands[0].imm==e:
   raw.append(hex(x.address))
 print('direct',hex(e),raw)
# atexit registrations for these dtors if any
for e in [0x629fd0,0x62a260,0x468670]:
 regs=[]
 for j,x in enumerate(ins):
  if x.address==0x7C978A and j>0:
   prev=ins[j-1]
   if prev.mnemonic=='call' and prev.operands and prev.operands[0].type==X86_OP_IMM and prev.operands[0].imm==e: regs.append(hex(x.address))
 print('atexit after call',hex(e),regs)
