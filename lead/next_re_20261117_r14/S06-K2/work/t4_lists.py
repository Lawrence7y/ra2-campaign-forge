"""
S06-K2 T4: comprehensive two-linked-list access scan.
Scan whole .text (skipdata) for [reg+0xe4]/[reg+0xe8] accesses where reg holds a CellClass*
(from CellClass methods' this, or GetCellAt return), plus [reg+0x30] (next) usage.
Attribute to functions via atlas intervals. Determine W/R for each head.
Also independently verify 0x47C620 (head A only) and 0x47E8A0 head selection.
Outputs EVIDENCE/t4_lists.txt
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections, bisect

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t4_lists.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas={}
with open(ATLAS) as f:
    next(f)
    for ln in f:
        q=ln.split('\t')
        if len(q)>=2:
            try: atlas[int(q[0],16)]=int(q[1])
            except: pass
starts=sorted(atlas)
def func_of(va):
    i=bisect.bisect_right(starts,va)-1
    if i<0: return None
    s=starts[i]; sz=atlas.get(s,0)
    if s<=va<s+sz and 0<sz<=0x8000: return s
    return None
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg','fstp','stosd','rep'}
def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'
CELL_VTS=[0x7e4ec0,0x7e4ec8,0x7e4ed0,0x7e4eec]
GETCELLAT=0x5657A0

p("="*72); p("S06-K2 T4 two linked lists [cell+0xE4]/[cell+0xE8], element +0x30=next"); p("="*72)

# Build cell* access scan over CellClass methods + GetCellAt windows
def scan_region(start,end,seed_reg,label,stop_ret=False):
    out=[]
    dm={seed_reg:0}
    for ins in disasm(start,end-start):
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rname(ops[1].reg); d=rname(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='lea' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            d=rname(ops[0].reg); m=ops[1].mem; b=rname(m.base) if m.base!=X86_REG_INVALID else None
            if b in dm: dm[d]=dm[b]+m.disp
            else: dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if d in dm: dm[d]+=ops[1].imm if mn=='add' else -ops[1].imm
        if mn=='call' and ops and ops[0].type==X86_OP_IMM and ops[0].imm==GETCELLAT: dm['eax']=0
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM: continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem; b=rname(m.base) if m.base!=X86_REG_INVALID else None
            idxr=rname(m.index) if m.index!=X86_REG_INVALID else None
            eff=None
            if b in dm and idxr is None: eff=dm[b]+m.disp
            if eff in (0xe4,0xe8,0x30):
                k='W' if (idx==0 and mn in WRITEMN) else 'R'
                out.append((eff,ins.address,k,mn,f"{ins.mnemonic} {ins.op_str}",label,func_of(ins.address)))
        if mn=='call':
            for r in ('eax','ecx','edx'): dm.pop(r,None)
        if stop_ret and mn=='ret': break
    return out

accesses=[]
# CellClass methods
methods=set()
for vt in CELL_VTS:
    for i in range(40):
        f=u32(vt+i*4)
        if f and section_of(f) and section_of(f)[4]=='.text': methods.add(f)
for f in [0x47bbf0,0x47bb60,0x483a00,0x485020,0x47ff80,0x5683c0,0x5687f0,0x47e8a0,0x47ea90,0x47c620]:
    methods.add(f)
for e in methods:
    sz=atlas.get(e,0x800); sz=sz if 0<sz<=0x2000 else 0x800
    accesses+=scan_region(e,e+sz,'ecx',f'cellfn:{e:#x}')
# GetCellAt windows
tlo,thi=text_bounds()
nsite=0
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==GETCELLAT:
        nsite+=1
        accesses+=scan_region(va,va+500,'eax',f'gca:{va:#x}')
p(f"scanned {len(methods)} CellClass methods + {nsite} GetCellAt windows")
for off in (0xe4,0xe8,0x30):
    rel=[a for a in accesses if a[0]==off]
    ws=[a for a in rel if a[2]=='W']; rs=[a for a in rel if a[2]=='R']
    p(f"\n[+{off:#x}] accesses={len(rel)} W={len(ws)} R={len(rs)}")
    for a in sorted(set(rel)):
        p(f"  {a[1]:#x} {a[2]} fn={a[6] and hex(a[6])} {a[5]:16} {a[4]}")
with open(OUT,'w') as f:
    f.write("S06-K2 T4 two linked-list accesses (cell* attributed)\n")
    for off in (0xe4,0xe8,0x30):
        f.write(f"\n# +{off:#x}\n")
        for a in sorted(set(x for x in accesses if x[0]==off)):
            f.write(f"{a[1]:#08x}\t{a[2]}\t{off:#x}\t{a[3]}\t{a[4]}\tfn={a[6] and hex(a[6])}\t{a[5]}\n")
p(f"\n[saved] {OUT}")
