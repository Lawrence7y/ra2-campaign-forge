import pathlib,struct,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_OP_REG
root=pathlib.Path(r"D:\Project\ra2-campaign-forge"); pe=pefile.PE(str(root/"ra2youli"/"gamemd.exe"),fast_load=False); ib=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def rvaoff(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
 return None
def u32(va):
 o=rvaoff(va-ib,4);return None if o is None else struct.unpack_from("<I",data,o)[0]
def cstr(va,n=200):
 o=rvaoff(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b"\x00")
 if z<0:return None
 try:return b[:z].decode("ascii")
 except:return None
def dis(va,n):
 o=rvaoff(va,n)
 md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
 return list(md.disasm(data[o:o+n],va)) if o is not None else []
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8,0x7e46f8,0x7ef8a4,0x7f0824]:
 print("\nVT",hex(vt))
 for i in range(-20,40):
  va=vt+4*i
  if i<0: val=u32(va); print(" pre",i,hex(va),hex(val) if val else None,repr(cstr(val) if val else None))
  else:
   val=u32(va); print(" slot",i,hex(va),hex(val) if val else None,repr(cstr(val) if val else None))
print("\nselect globals with context")
for g in [0xa8ed84,0xb0f5b8,0xb0f5bc,0xb0f5c0,0xb0f5c5,0xb0f5c8,0xb0f5cc,0x89de30,0x89de34,0x89de38,0xac4948,0xac494c,0xac4950]:
 o=rvaoff(g-ib,16)
 print(hex(g), data[o:o+16].hex() if o else None, [hex(x) for x in struct.unpack_from('<4I',data,o)] if o else None)
