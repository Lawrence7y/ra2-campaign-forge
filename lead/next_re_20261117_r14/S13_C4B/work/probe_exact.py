import pathlib,struct,hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_OP_REG
root=pathlib.Path(r"D:\Project\ra2-campaign-forge")
target=root/"ra2youli"/"gamemd.exe"
pe=pefile.PE(str(target),fast_load=False); ib=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def off(va,n=4):
 r=va-ib
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:
   return s.PointerToRawData+(r-s.VirtualAddress)
 return None
def u32(va):
 o=off(va,4); return None if o is None else struct.unpack_from("<I",data,o)[0]
def cs(va,n=160):
 o=off(va,1)
 if o is None:return None
 b=data[o:o+n]; z=b.find(b"\x00")
 if z<0:return None
 try:return b[:z].decode("ascii")
 except:return None
def dis(va,n):
 o=off(va,n)
 md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
 return list(md.disasm(data[o:o+n],va)) if o is not None else []
def vtable(va):
 out=[]
 for i in range(0,32): out.append(u32(va+4*i))
 return out
entries=[0x468670,0x629fd0,0x62a260]
for e in entries:
 vt=None
 for s in pe.sections:
  if s.Name.rstrip(b"\x00")==b".text":continue
  o=s.PointerToRawData
  for p in range(o,o+s.SizeOfRawData-3,4):
   if struct.unpack_from("<I",data,p)[0]==e:
    vt=ib+s.VirtualAddress+(p-o);break
  if vt:break
 col=vt-4; td=u32(col+0xC); name=cs(td+8) if td else None
 slots=vtable(vt)
 print("\n=== ENTRY",hex(e),"VT",hex(vt) if vt else None,"COL",hex(col) if col else None,"TD",hex(td) if td else None,"RTTI",name)
 print("slots",[None if x is None else hex(x) for x in slots])
 if vt:
  for i,v in enumerate(slots[:8]):
   if v and v in entries: print("  slot",i,"is another selected entry",hex(v))
 # find exact dispatch sites in full text at instruction boundaries: call [reg+disp] preceded by mov ecx,global and mov reg,[global]
 md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
 text=next(s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text")
 ins=list(md.disasm(data[text.PointerToRawData:text.PointerToRawData+min(text.SizeOfRawData,text.Misc_VirtualSize)],ib+text.VirtualAddress))
 sitehits=[]
 for j,x in enumerate(ins):
  if x.mnemonic!="call" or not x.operands or x.operands[0].type!=X86_OP_MEM: continue
  m=x.operands[0].mem
  if m.base==0 or m.index!=0: continue
  disp=m.disp
  prev=ins[j-1] if j else None; prev2=ins[j-2] if j>1 else None
  def absop(i,opn):
   if not i or len(i.operands)<=opn:return None
   op=i.operands[opn]
   if op.type==X86_OP_IMM and 0x400000<=op.imm<0x10000000:return op.imm
   if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and 0x400000<=op.mem.disp<0x10000000:return op.mem.disp
   return None
  g=None
  if prev and prev.mnemonic=="mov" and absop(prev,0) and prev.operands[0].type==X86_OP_REG:
   g=absop(prev,1)
  elif prev and prev.mnemonic=="mov" and prev.operands[0].type==X86_OP_MEM:
   g=absop(prev,0)
  if g and prev2 and prev2.mnemonic=="mov" and absop(prev2,1):
   g2=absop(prev2,0) or absop(prev2,1)
   if g2: g=g2
  if g and u32(g) in range(ib,ib+0x800000):
   val=u32(u32(g)+disp)
   if val==e:
    sitehits.append((hex(x.address),hex(g),hex(u32(g)),disp,hex(u32(g)+disp),x.mnemonic+" "+x.op_str, prev.mnemonic+" "+prev.op_str if prev else "", prev2.mnemonic+" "+prev2.op_str if prev2 else ""))
 print("exact-like sites",sitehits[:20])
