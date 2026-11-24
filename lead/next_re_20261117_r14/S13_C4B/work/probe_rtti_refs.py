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
# locate all aligned dword references to selected VTs anywhere in file-backed sections
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8]:
 refs=[]
 for s in pe.sections:
  for p in range(s.PointerToRawData,s.PointerToRawData+s.SizeOfRawData-3,4):
   if struct.unpack_from("<I",data,p)[0]==vt:
    va=ib+s.VirtualAddress+(p-s.PointerToRawData)
    refs.append((s.Name.rstrip(b"\x00").decode(errors="replace"),hex(va)))
 print("VT",hex(vt),"refs",refs[:50],"count",len(refs))
# find RTTI COL/TD by scanning for COL whose vt-relative fields match vt slots 0/1 etc. print candidates with plausible td pointer to .rdata and name
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8]:
 cands=[]
 for va in range(0x7e1000,0x7e4100,4):
  col=u32(va)
  if col is None:continue
  td=u32(col+0xc) if col else None
  if td is None or not (0x7e1000<=td<0x7e4100):continue
  nm=cstr(td+8)
  if nm and nm.startswith(".?AV"):
   slots=[u32(vt+4*i) for i in range(0,16)]
   score=sum(1 for s in slots if s==col)
   if score:
    cands.append((score,hex(va),hex(col),hex(td),nm))
 print("RTTI candidates",hex(vt),sorted(cands,reverse=True)[:10])
# raw disassembly around candidate entries
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
for e,n in [(0x468670,0x100),(0x629fd0,0x120),(0x62a260,0x180)]:
 o=rvaoff(e-ib,n)
 print("\nDIS",hex(e))
 for i in md.disasm(data[o:o+n],e):print(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str)
