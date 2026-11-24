# Channel A FINAL: exhaustive exact dispatch scan, both orders, all regs.
# exact := (mov rthis, IMM_G) AND (mov rvt, [IMM_G]) AND (call [rvt+disp]) within small window, ecx==rthis.
# Key: global G is an OBJECT (its [G] is vptr) because some C7 05 [G],vt writes exist.
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
from capstone.x86 import *
T0,T1=text_range(); code=rd(T0,T1-T0)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(code,T0))
def ops(i):
    if i.id==X86_INS_INVALID: return []
    try:return i.operands
    except:return []

# Globals that are vptr-holding objects: those with C7 05 [G],<rdata vtable> writes (direct or via regs we'll add later)
GOBJS=set()
for n,v,vs,pr,rs in SECS:
    if n!='.text':continue
    pr0=pr;end=pr+min(vs,rs);i=DATA.find(b'\xc7\x05',pr0,end)
    while i!=-1 and i+10<=end:
        g,imm=struct.unpack('<II',DATA[i+2:i+10])
        if 0x7e1000<=imm<0x810000: GOBJS.add(g)
        i=DATA.find(b'\xc7\x05',i+1,end)
print('vptr-holding globals (C7 05 direct)',len(GOBJS))

# Compute windows: for each call [reg+disp], search backwards up to 8 insns for
#   (a) mov reg,[G]  where G in GOBJS
#   (b) mov ecx,G    (imm == same G) OR lea ecx,[G]? just imm
# record vptr content by reading file bytes at G if mapped.
def regname(i,idx):
    o=ops(i)
    return o[idx].reg if len(o)>idx and o[idx].type==X86_OP_REG else None

hits=[]
for ci,c in enumerate(insns):
    o=ops(c)
    if c.id!=X86_INS_CALL or not o or o[0].type!=X86_OP_MEM: continue
    base=o[0].mem.base; disp=o[0].mem.disp
    if base is None: continue
    # look back for mov base,[G]
    vinfo=None; cinfo=None
    for k in range(max(0,ci-10),ci):
        p=insns[k]; po=ops(p)
        if p.id==X86_INS_MOV and len(po)>=2 and po[0].type==X86_OP_REG and po[0].reg==base and po[1].type==X86_OP_MEM and po[1].mem.base==0 and po[1].mem.index==0:
            G=po[1].mem.disp&0xffffffff
            if G in GOBJS: vinfo=(p.address,G)
        if p.id==X86_INS_MOV and len(po)>=2 and po[0].type==X86_OP_REG and po[0].reg==X86_REG_ECX and po[1].type==X86_OP_IMM:
            g=po[1].imm&0xffffffff
            if g in GOBJS: cinfo=(p.address,g)
    if vinfo and cinfo and vinfo[1]==cinfo[1]:
        G=vinfo[1]
        d=dict(call_site=c.address,slot_byte=disp,slot_div4=(disp//4 if disp%4==0 else None),vptr_load=vinfo[0],ecx_load=cinfo[0],g=hex(G),vptr_file=u32(G))
        hits.append(d)
print('exact hits (C7 05-global objects):',len(hits))
from collections import Counter
print('by global',Counter(h['g'] for h in hits))
json.dump(hits,open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelA_exact2.json','w'),indent=1)
for h in hits[:60]: print(h)
