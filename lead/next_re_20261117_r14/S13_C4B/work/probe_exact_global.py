import pathlib,struct,json
import pefile
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
# collect vt refs from all aligned dwords and classify vtable-like by prior dword being pointer to .rdata / COL candidate
def refs_to(v):
 out=[]
 for s in pe.sections:
  for p in range(s.PointerToRawData,s.PointerToRawData+s.SizeOfRawData-3,4):
   if struct.unpack_from("<I",data,p)[0]==v:
    out.append(ib+s.VirtualAddress+(p-s.PointerToRawData))
 return out
cands={}
for e in [0x468670,0x629fd0,0x62a260,0x46ae70]:
 for va in refs_to(e):
  # candidate vt base va; COL at va-4; TD at [COL+0xC]; RTTI name at TD+8
  col=u32(va-4); td=u32(col+0xc) if col else None; nm=cstr(td+8) if td else None
  if nm and nm.startswith(".?AV"):
   cands[e]=(va,col,td,nm)
  else:
   cands.setdefault(e,[])
 print(hex(e),'refs',len(refs_to(e)),'cand',cands[e])
# find exact dispatch via global load + slot, requiring global vptr from any mov [g],vt anywhere in .text, no atexit classification yet
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_OP_REG
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
text=next(s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text")
ins=list(md.disasm(data[text.PointerToRawData:text.PointerToRawData+min(text.SizeOfRawData,text.Misc_VirtualSize)],ib+text.VirtualAddress))
vt_by_g={}
for x in ins:
 if x.mnemonic=='mov' and len(x.operands)==2:
  a,b=x.operands
  if a.type==X86_OP_MEM and a.mem.base==0 and a.mem.index==0 and b.type==X86_OP_IMM and 0x400000<=a.mem.disp<0xC00000 and 0x400000<=b.imm<0x810000:
   vt_by_g.setdefault(a.mem.disp,set()).add((b.imm,x.address))
def absv(op):
 if op.type==X86_OP_IMM and 0x400000<=op.imm<0xC00000:return op.imm
 if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and 0x400000<=op.mem.disp<0xC00000:return op.mem.disp
 return None
for e in [0x468670,0x629fd0,0x62a260]:
 hits=[]
 for j,x in enumerate(ins):
  if x.mnemonic!='call' or not x.operands or x.operands[0].type!=X86_OP_MEM or x.operands[0].mem.base==0 or x.operands[0].mem.index!=0:continue
  disp=x.operands[0].mem.disp; window=ins[max(0,j-3):j]
  g=None; ecxg=None
  for y in window:
   if y.mnemonic=='mov' and len(y.operands)==2:
    a,b=y.operands
    if a.type==X86_OP_MEM and a.mem.base==0 and b.type==X86_OP_IMM:
     gg=absv(a)
     if gg and b.imm==0: ecxg=gg
    if a.type==X86_OP_REG and b.type==X86_OP_MEM:
     gg=absv(b)
     if gg: g=gg
    if a.type==X86_OP_MEM and b.type==X86_OP_IMM:
     gg=absv(a)
     if gg: g=gg
  if g and g in vt_by_g:
   for vt,st in vt_by_g[g]:
    if u32(vt+disp)==e:
     hits.append((hex(x.address),hex(g),hex(vt),disp,hex(st)))
 print('hits',hex(e),hits[:20],len(hits))
