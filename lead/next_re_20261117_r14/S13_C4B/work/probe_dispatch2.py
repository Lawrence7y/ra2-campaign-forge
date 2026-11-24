import pathlib,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_OP_REG
root=pathlib.Path(r"D:\Project\ra2-campaign-forge"); target=root/"ra2youli"/"gamemd.exe"
pe=pefile.PE(str(target),fast_load=False); ib=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def rvaoff(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u32(va):
 o=rvaoff(va-ib,4);return None if o is None else struct.unpack_from("<I",data,o)[0]
def cs(va,n=200):
 o=rvaoff(va-ib,1)
 if o is None:return None
 b=data[o:o+n]; z=b.find(b"\x00")
 if z<0:return None
 try:return b[:z].decode("ascii")
 except:return None
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
text=next(s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text")
ins=list(md.disasm(data[text.PointerToRawData:text.PointerToRawData+min(text.SizeOfRawData,text.Misc_VirtualSize)],ib+text.VirtualAddress))
def absval(i,side):
 if not i:return None
 for op in i.operands if side=="any" else [i.operands[side]]:
  if op.type==X86_OP_IMM and 0x400000<=op.imm<0x10000000:return op.imm
  if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and 0x400000<=op.mem.disp<0x10000000:return op.mem.disp
 return None
def iscallmem(i):
 return i and i.mnemonic=="call" and i.operands and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.base!=0 and i.operands[0].mem.index==0
# collect globals written vptr to targets
vt_by_g={}
for j,x in enumerate(ins):
 if x.mnemonic=="mov" and len(x.operands)==2 and x.operands[0].type==X86_OP_MEM and x.operands[0].mem.base==0 and x.operands[0].mem.index==0 and x.operands[1].type==X86_OP_IMM:
  g=x.operands[0].mem.disp; vt=x.operands[1].imm
  if 0x400000<=g<0xC00000 and 0x400000<=vt<0x810000: vt_by_g.setdefault(g,set()).add((vt,x.address))
for e in [0x468670,0x629fd0,0x62a260]:
 hits=[]; soft=[]
 for j,x in enumerate(ins):
  if not iscallmem(x):continue
  disp=x.operands[0].mem.disp
  # 4 preceding windows; find global loaded and ecx set to same or another global
  w=ins[max(0,j-5):j]
  glist=[]
  for y in w:
   if y.mnemonic=="mov" and len(y.operands)==2:
    a,b=y.operands
    if a.type==X86_OP_REG and b.type==X86_OP_MEM and b.mem.base==0 and b.mem.index==0 and 0x400000<=b.mem.disp<0xC00000: glist.append(("load",y.address,b.mem.disp,a.reg))
    if a.type==X86_OP_MEM and a.mem.base==0 and a.mem.index==0 and b.type==X86_OP_IMM and 0x400000<=a.mem.disp<0xC00000: glist.append(("movimm",y.address,a.mem.disp,b.imm))
    if a.type==X86_OP_REG and b.type==X86_OP_IMM and 0x400000<=b.imm<0xC00000: glist.append(("immreg",y.address,b.imm,a.reg))
  for k,g in enumerate([q[2] for q in glist]):
   for vt,st in vt_by_g.get(g,[]):
    val=u32(vt+disp)
    if val==e:
     hits.append((hex(x.address),hex(g),hex(vt),disp,hex(st),"|".join(q[0]+":"+hex(q[1])+":"+hex(q[2]) for q in glist)))
    elif disp<0x100 and val is not None and 0x400000<=val<0x810000 and val in [q[2] for q in glist]:
     soft.append((hex(x.address),hex(g),hex(vt),disp,hex(val)))
 print("ENTRY",hex(e),"hits",len(hits))
 for h in hits[:20]:print(" ",h)
 print(" soft",len(soft),soft[:10])
