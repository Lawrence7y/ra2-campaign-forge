
import pefile
from capstone import *
from capstone.x86 import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[(s.Name.rstrip(b'\x00').decode('latin1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def read(va,n):
    for n_,b,vs,pr,rs in secs:
        if b<=va<b+max(vs,rs): return raw[pr+(va-b):pr+(va-b)+n]
    return b''
def dword(va):
    b=read(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
def rtti(vt):
    col=dword(vt-4)
    if not col: return None
    td=dword(col+0xC)
    if not td: return None
    return read(td+8,120).split(b'\x00')[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
for fn in (0x578080,0x586360,0x5864a0,0x50b6f0,0x4f9a90,0x487690,0x5678e0):
    ins=[i for i in md.disasm(read(fn,600),fn) if i.id!=0]
    vts=[]
    for i in ins:
        o=i.operands
        if i.mnemonic=='mov' and len(o)==2 and o[0].type==CS_OP_MEM and o[1].type==CS_OP_IMM and 0x7e0000<=o[1].imm<0x840000:
            nm=rtti(o[1].imm)
            if nm: vts.append((hex(i.address),i.reg_name(o[0].mem.base),o[0].mem.disp,hex(o[1].imm),nm))
    first=[('%08X %s %s'%(i.address,i.mnemonic,i.op_str)) for i in ins[:6]]
    print(hex(fn),'n_insns',len(ins),'vts',vts[:6])
    print('   ','; '.join(first))
