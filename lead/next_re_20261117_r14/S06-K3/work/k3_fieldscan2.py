"""S06-K3 T2 field scan V2: exhaustive per-function provenance scan.
For EVERY atlas function, track cell* provenance seeded by:
  (S1) call GetCellAt 0x5657A0 -> eax = cell*
  (S2) mov reg,[0x87F924] (cell-array ptr) then mov x,[reg+idx*4] -> x = cell*
  (S3) mov reg, 0xABDC50 (INVALIDCELL singleton is a CellClass)
  (S4) this=ecx inside the 42-method CellClass set
Record genuine [cell+off] reads/writes for the 63 offsets. Exclude virtual calls,
lea, and absolute-addressed (non-cell) operands. Two access forms covered.
Outputs EVIDENCE/k3_fieldscan2.tsv + k3_fieldscan2.txt
"""
from lib import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE\k3_fieldscan2.tsv"
TXT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE\k3_fieldscan2.txt"

OFF63 = set([0x24,0x26,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,
0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,0x11c,
0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140])
GETCELLAT=0x5657A0
INVALIDCELL=0xABDC50
CELLARRPTR=0x87F924
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','sar',
         'imul','neg','not','xchg','fstp','fst','fistp'}
SKIP={'lea','nop','pref','cdq','cld','std','clc','stc'}

CELL_VTS=[0x7E4EC0,0x7E4EC8,0x7E4ED0,0x7E4EEC]
vtf=[]
for vt in CELL_VTS:
    for i in range(48):
        f=u32(vt+i*4)
        if f is None or not in_text(f): break
        vtf.append(f)
NONVIRT=set([0x47BBF0,0x47BB60,0x483A00,0x485020,0x47FF80,0x5683C0,0x5687F0,0x47E8A0,0x47EA90,0x5657A0])
METHODS=set(vtf)|NONVIRT

writes=collections.defaultdict(list)
reads=collections.defaultdict(list)
vc_excluded=0
scan_sites=collections.Counter()

def scan_func(entry, end, is_method):
    global vc_excluded
    dm={}
    if is_method: dm['ecx']=('cell',0)
    for ins in disasm(entry, end-entry):
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='call' and ops and ops[0].type==X86_OP_IMM and ops[0].imm==GETCELLAT:
            dm['eax']=('cell',0); scan_sites['S1_gca']+=1
        # mov reg,[0x87F924] -> arrptr  (absolute addressing form)
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            m=ops[1].mem
            if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID and m.disp==CELLARRPTR:
                dm[rn(ops[0].reg)]=('arrptr',0); scan_sites['S2a_arrptr']+=1
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rn(ops[1].reg); d=rn(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rn(ops[0].reg)
            if ops[1].imm==INVALIDCELL: dm[d]=('cell',0); scan_sites['S3_invalidcell']+=1
            else: dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rn(ops[0].reg)
            if d in dm:
                k,dl=dm[d]; dm[d]=(k, dl+(ops[1].imm if mn=='add' else -ops[1].imm))
        # mov x,[arrptr + idx*4] -> cell*
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            m=ops[1].mem
            b=rn(m.base) if m.base!=X86_REG_INVALID else None
            if b in dm and dm[b][0]=='arrptr':
                dm[rn(ops[0].reg)]=('cell',0); scan_sites['S2b_elem']+=1
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            vc_excluded+=1
            for reg in ('eax','ecx','edx'): dm.pop(reg,None)
            continue
        if mn in SKIP: continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            if m.base==X86_REG_INVALID: continue
            b=rn(m.base)
            if b not in dm or dm[b][0]!='cell': continue
            if m.index!=X86_REG_INVALID: continue
            eff=dm[b][1]+m.disp
            if eff not in OFF63: continue
            insn=f"{ins.mnemonic} {ins.op_str}"
            if idx==0 and mn in WRITEMN:
                writes[eff].append((ins.address,entry,insn))
            else:
                reads[eff].append((ins.address,entry,insn,mn))
        if mn=='call':
            for reg in ('eax','ecx','edx'): dm.pop(reg,None)

entries=sorted(atlas.items())
print(f"atlas functions = {len(entries)}")
for e,sz in entries:
    if sz<=0 or sz>0x2000: continue
    scan_func(e, e+sz, e in METHODS)
print(f"virtual/extra call [mem] excluded = {vc_excluded}")
print("seed firings:", dict(scan_sites))

def dedup(lst):
    seen=set(); out=[]
    for t in lst:
        k=(t[0],t[2])
        if k in seen: continue
        seen.add(k); out.append(t)
    return sorted(out,key=lambda x:x[0])

lines=["offset\tW_count\tR_count\tstrong(W1R3)\twrite_sites\tread_sites"]
txt=[]
strong=[]
for o in sorted(OFF63):
    w=dedup(writes.get(o,[])); r=dedup(reads.get(o,[]))
    st='Y' if (len(w)>=1 and len(r)>=3) else 'n'
    if st=='Y': strong.append(o)
    ws=','.join(f'{x[0]:#x}' for x in w[:20]); rs=','.join(f'{x[0]:#x}' for x in r[:20])
    lines.append(f"{o:#06x}\t{len(w)}\t{len(r)}\t{st}\t{ws}\t{rs}")
    txt.append(f"{o:#06x} W={len(w):3d} R={len(r):3d} strong={st}")
with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
with open(TXT,'w',encoding='utf-8') as f: f.write('\n'.join(txt)+'\n')
print(f"STRONG (W>=1 & R>=3) = {len(strong)}: "+', '.join(hex(x) for x in strong))
print(f"[saved] {OUT}\n[saved] {TXT}")
