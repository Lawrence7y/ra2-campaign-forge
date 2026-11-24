"""T4: layout boundary self-check. Max proved field off+width <= GetSize;
and ctor field-init writes within [this, this+GetSize)."""
import pefile, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'ra2youli','gamemd.exe')
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b'\0').decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
DATA=open(P,'rb').read(); MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None
def dis_range(va,n=400):
    o=off(va); out=[]
    for ins in MD.disasm(DATA[o:o+4000],va):
        out.append(ins)
        if len(out)>=n: break
    return out
# ctor entry -> (class, getsize); scan first 120 insns for writes to [esi/edi/ecx/eax + disp] with this-base regs
CTORS=[(0x43B740,'BuildingClass',0x720,0x43B9FA),(0x7353C0,'UnitClass',0x8E8,0x73543A),
       (0x517A50,'InfantryClass',0x6F0,0x517ACC),(0x413D20,'AircraftClass',0x6D8,0x413D87),
       (0x6F2B40,'TechnoClass',None,0x6F3130)]
for entry,nm,sz,vwrite in CTORS:
    insns=dis_range(entry,150)
    writes=[]
    this_regs={'esi','edi','ecx','ebx'}
    for ins in insns:
        if ins.address>vwrite+0x30: break
        try: ops=ins.operands
        except: continue
        if not ops: continue
        op=ops[0]
        if op.type==X86_OP_MEM and op.mem.disp>0 and ins.mnemonic in ('mov','movzx','movsx'):
            b=ins.reg_name(op.mem.base) if op.mem.base else None
            if b in this_regs:
                writes.append((ins.address,ins.mnemonic,ins.op_str,op.mem.disp,op.size))
    maxoff=max([w[3] for w in writes],default=0)
    print('=== %s ctor=%08X getsize=%s vwrite=%08X this-writes=%d maxdisp=%s(0x%X) ==='%(
        nm,entry,('0x%X'%sz) if sz else 'STUB',vwrite,len(writes),('0x%X'%maxoff),maxoff))
    if sz:
        over=[w for w in writes if w[3]+w[4]>sz]
        print('   writes beyond GetSize:',len(over))
        if over:
            for w in over[:8]: print('     OVER',('%08X'%w[0]),w[1],w[2])
    for w in writes[:12]:
        print('   %08X %s %s'%(w[0],w[1],w[2]))
