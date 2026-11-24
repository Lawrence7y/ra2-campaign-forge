# Channel A v2: exact dispatch = mov ecx,<imm32 G>; (few insns) mov edx,[G]; call [edx+slot]
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
from capstone.x86 import *
T0,T1=text_range(); code=rd(T0,T1-T0)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(code,T0)); N=len(insns)
print('insns',N)
def is_mov_ecx_imm(i):
    return i.id==X86_INS_MOV and len(i.operands)>=2 and i.operands[0].type==X86_OP_REG and i.operands[0].reg==X86_REG_ECX and i.operands[1].type==X86_OP_IMM
def is_mov_edx_abs(i):
    return i.id==X86_INS_MOV and i.operands[0].type==X86_OP_REG and i.operands[0].reg==X86_REG_EDX and i.operands[1].type==X86_OP_MEM and i.operands[1].mem.base==0 and i.operands[1].mem.index==0
def call_mem_base(i,base):
    return i.id==X86_INS_CALL and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.base==base

hits=[]
# exact sequence: mov ecx,<G> ; mov edx,[G] ; call [edx+disp] contiguous
for k in range(N-2):
    a,b,c=insns[k],insns[k+1],insns[k+2]
    if b.address!=a.address+a.size or c.address!=b.address+b.size: continue
    if not is_mov_ecx_imm(a): continue
    if not is_mov_edx_abs(b): continue
    if not call_mem_base(c,X86_REG_EDX): continue
    G=a.operands[1].imm & 0xffffffff
    G2=b.operands[1].mem.disp & 0xffffffff
    slot=c.operands[0].mem.disp
    hits.append(dict(pattern='contig',ecx_site=a.address,edx_site=b.address,call_site=c.address,G=hex(G),G2=hex(G2),same=(G==G2),slot=slot,vptr=u32(G2),bytes=a.bytes.hex()+' '+b.bytes.hex()+' '+c.bytes.hex()))
# sequence with 1-3 intervening insns between mov ecx and mov edx
for k in range(N-6):
    a=insns[k]
    if not is_mov_ecx_imm(a): continue
    G=a.operands[1].imm & 0xffffffff
    for j in range(k+1,min(k+5,N)):
        b=insns[j]
        if not is_mov_edx_abs(b): continue
        G2=b.operands[1].mem.disp & 0xffffffff
        if G!=G2: continue
        # call must be immediate next after b, or within 3 with no clobber of edx (we'll mark gap)
        for cidx in range(j+1,min(j+4,N)):
            c=insns[cidx]
            if call_mem_base(c,X86_REG_EDX):
                hits.append(dict(pattern='gap%d'%(j-k-1),ecx_site=a.address,edx_site=b.address,call_site=c.address,G=hex(G),G2=hex(G2),same=True,slot=c.operands[0].mem.disp,vptr=u32(G2),bytes=a.bytes.hex()+' '+b.bytes.hex()+' '+c.bytes.hex()))
                break
            if c.id==X86_INS_MOV and c.operands[0].type==X86_OP_REG and c.operands[0].reg==X86_REG_EDX: break
        break
# dedupe
un={}
for h in hits: un[(h['ecx_site'],h['edx_site'],h['call_site'])]=h
hits=list(un.values())
print('total exact hits',len(hits),'contig',sum(1 for h in hits if h['pattern']=='contig'))
json.dump(hits,open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelA_exact.json','w'),indent=1)
# group by vptr
from collections import Counter
c=Counter(hex(h['vptr']) for h in hits)
print('distinct vptrs',len(c))
for vp,n in c.most_common(40): print(vp,n)
