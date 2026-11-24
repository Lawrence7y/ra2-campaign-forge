# Channel A: capstone instruction-boundary scan for exact virtual dispatch
# Pattern: mov ecx,[abs_global]; mov edx,[abs_global]; call [edx+disp] ; where both globals are the same object pointer
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
from capstone.x86 import *

T0,T1=text_range()
code=rd(T0,T1-T0)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

# single linear sweep at instruction boundaries (function-agnostic)
insns=[]
for i in md.disasm(code,T0):
    insns.append(i)
print('total instructions',len(insns),'skipdata count',sum(1 for i in insns if i.id==X86_INS_INVALID))
# build index by address
byaddr={i.address:k for k,i in enumerate(insns)}

# find 'mov ecx,[abs]' and 'mov edx,[abs]' : A1 imm32 (mov eax,[abs]) or 8B 0D/15 imm32
def mem_abs(i):
    # returns absolute address if operand is [abs32], else None
    for op in i.operands:
        if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0:
            return op.mem.disp & 0xffffffff
    return None

def is_mov_reg_abs(i,reg):
    return i.id==X86_INS_MOV and i.operands[0].type==X86_OP_REG and i.operands[0].reg==reg and i.operands[1].type==X86_OP_MEM and i.operands[1].mem.base==0 and i.operands[1].mem.index==0

# collect candidate sequences: i, i+1 = mov edx,[abs]; i+2 = call [edx+disp]
hits=[]
N=len(insns)
for k in range(N-2):
    a,b,c=insns[k],insns[k+1],insns[k+2]
    # require contiguous (next address == prev address + size)
    if b.address!=a.address+a.size or c.address!=b.address+b.size: continue
    # mov ecx,[abs] or mov edx,[abs] in a; mov edx,[abs] in b (edx loaded)
    if not (is_mov_reg_abs(b,X86_REG_EDX)): continue
    # call [edx+disp] in c
    if c.id!=X86_INS_CALL: continue
    op=c.operands[0]
    if op.type!=X86_OP_MEM: continue
    if op.mem.base!=X86_REG_EDX: continue
    disp=op.mem.disp
    g=b.operands[1].mem.disp & 0xffffffff
    # find preceding mov ecx,[abs] within 4 insns, contiguous
    g_ecx=None; mov_ecx_site=None
    for d in range(1,5):
        if k-d<0: break
        p=insns[k-d]
        if p.address+d!=-1 and insns[k-d+1].address==p.address+p.size or True:
            pass
        if is_mov_reg_abs(p,X86_REG_ECX):
            g_ecx=p.operands[1].mem.disp & 0xffffffff
            mov_ecx_site=p.address
            break
        # also accept 'mov ecx,[eax]' where eax loaded from global? not exact - skip
    hits.append(dict(call_site=c.address,edx_load=b.address,edx_global=hex(g),ecx_load=mov_ecx_site,ecx_global=hex(g_ecx) if g_ecx else None,slot=disp,ecx_same=(g_ecx==g),insn_bytes=' '.join(x.bytes.hex() for x in (a,b,c))))
print('total exact-ish sequences (mov edx,[abs];call [edx+disp])',len(hits))
print('with preceding mov ecx,[abs] contiguous',sum(1 for h in hits if h['ecx_load']))
# filter: ecx and edx global same
same=[h for h in hits if h['ecx_same']]
print('same global ecx/edx',len(same))
for h in same[:80]: print(h)
json.dump(dict(hits=hits,same=same),open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelA_raw.json','w'),indent=1)
