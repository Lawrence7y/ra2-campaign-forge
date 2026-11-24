"""Verify: at push<size> allocation sites, after call operator_new, ecx=eax then call ctor."""
import pefile, struct, os, bisect
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'ra2youli','gamemd.exe')
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b'\0').decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
DATA=open(P,'rb').read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None
def dis(va,n=40):
    o=off(va); out=[]
    for ins in MD.disasm(DATA[o:o+200],va):
        out.append(ins)
        if len(out)>=n: break
    return out
def regname(ins,opidx):
    try:
        op=ins.operands[opidx]
        if op.type==X86_OP_REG: return ins.reg_name(op.reg)
    except: pass
    return None

# (class,size,push_site,expected_ctor)
CASES=[
 ('BuildingClass',0x720,0x44FAF8,0x43B740),
 ('UnitClass',0x8E8,0x449E16,0x7353C0),
 ('InfantryClass',0x6F0,0x4430C2,0x517A50),
 ('AircraftClass',0x6D8,0x41B1B4,0x413D20),
]
for nm,sz,site,ctor in CASES:
    insns=dis(site,40)
    print('=== %s push@%08X expect_ctor=%08X ==='%(nm,site,ctor))
    seen_new=False; ecx_eax=False
    for ins in insns:
        txt=ins.mnemonic+' '+ins.op_str
        mark=''
        if ins.mnemonic=='call':
            try:
                op=ins.operands[0]
                if op.type==X86_OP_IMM and op.imm==0x7C8E17:
                    seen_new=True; mark=' <== operator new'
                if op.type==X86_OP_IMM and op.imm==ctor:
                    mark=' <== CTOR call' + (' [ecx=eax before]' if ecx_eax else ' [NO ecx=eax tracked]')
            except: pass
        if ins.mnemonic=='mov' and len(ins.op_str.split(','))==2:
            dst,d1=[x.strip() for x in ins.op_str.split(',',1)]
            if dst=='ecx' and d1=='eax':
                ecx_eax=True; mark=' <== ecx=eax'
        print('  %08X %-22s %s%s'%(ins.address,ins.bytes.hex(),txt,mark))
