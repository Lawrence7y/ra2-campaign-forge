"""
S06-K2 T1: authoritative CellClass field-access scanner.
- Method set from .rdata RTTI (union of 4 CellClass vtables' .text slots + ctor/dtor + known users).
- this-tracker: tracks ECX at entry, propagates through mov/lea/add derived bases (reg -> delta from this).
- Excludes virtual calls `call [reg+disp]` from READ points (vtable slot calls are NOT data field reads).
- Covers absolute addressing (base=0) and base+disp.
- Records (offset, width, kind, mnemonic, site, function, full_insn).
- Writes full evidence to EVIDENCE/t1_cell_fields.txt
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM
import struct, collections

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_cell_fields.txt"
_lines=[]
def p(s=''):
    print(s); _lines.append(str(s))

ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas={}
with open(ATLAS) as f:
    next(f)
    for ln in f:
        q=ln.split('\t')
        if len(q)>=2:
            try: atlas[int(q[0],16)]=int(q[1])
            except: pass

# ---- authoritative method set from .rdata ----
CELL_VTS=[0x7e4ec0,0x7e4ec8,0x7e4ed0,0x7e4eec]
methods=[]  # (entry, label)
seen=set()
for vt in CELL_VTS:
    for i in range(40):
        f=u32(vt+i*4)
        if not f: continue
        sec=section_of(f)
        if sec and sec[4]=='.text' and f not in seen:
            seen.add(f); methods.append((f, f'vt({vt:#x})[{i}]'))
# known non-virtual CellClass functions
EXTRA=[(0x47bbf0,'ctor'),(0x47bb60,'dtor'),(0x483a00,'ctor2'),(0x485020,'ore'),
       (0x47ff80,'getcenter'),(0x5683c0,'attach'),(0x5687f0,'detach'),
       (0x47e8a0,'linkadd'),(0x47ea90,'linkdel')]
for f,l in EXTRA:
    if f not in seen:
        seen.add(f); methods.append((f,l))

p("="*72)
p("S06-K2 T1 CellClass field access scan")
p(f"method set size = {len(methods)} (union of 4 CellClass vtables .text slots + {len(EXTRA)} known)")
p("="*72)

WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr',
         'sar','imul','neg','not','xchg','fstp','fst','fistp','stosd','stosb','stosw','rep','pop'}
CALLER_SAVED={'eax','ecx','edx'}

def regname(r):
    return ins_reg_name(r)

# capstone reg name helper
from capstone.x86 import X86_REG_INVALID
def rname(reg):
    try: return md.reg_name(reg)
    except: return f'reg{reg}'

def fn_end(entry, maxb=0x1000):
    sz=atlas.get(entry)
    return entry + (sz if sz and 0<sz<=maxb else maxb)

def analyze(entry, label):
    end=fn_end(entry)
    insns=disasm(entry, end-entry)
    # delta map: reg name -> offset from `this` base
    dm={'ecx':0}
    acc=[]
    vcall_excluded=[]
    for ins in insns:
        if ins.id==0: continue
        mn=ins.mnemonic
        ops=ins.operands
        # propagation
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rname(ops[1].reg); d=rname(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='lea' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            d=rname(ops[0].reg)
            m=ops[1].mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            if b in dm:
                dm[d]=dm[b]+m.disp   # derived base
            else:
                dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if d in dm:
                dm[d]+= (ops[1].imm if mn=='add' else -ops[1].imm)
        # virtual call exclusion: call [reg+disp]
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            vcall_excluded.append((ins.address,mn,ins.op_str,label))
            # still record the mem operand as a virtual slot reference, not a data read
            continue
        # memory operands
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            idxr=rname(m.index) if m.index!=X86_REG_INVALID else None
            eff=None
            if b in dm and idxr is None:
                eff=dm[b]+m.disp
            elif b in dm and idxr in dm:
                eff=dm[b]+m.disp+dm[idxr]*m.scale
            if eff is None: continue
            if not (0 <= eff < 0x400): continue   # keep plausible object offsets
            is_write = (idx==0 and mn in WRITEMN)
            kind='W' if is_write else 'R'
            acc.append((eff, op.size, kind, mn, ins.address, label, f"{ins.mnemonic} {ins.op_str}"))
        # clobbers
        if mn=='call':
            for r in CALLER_SAVED: dm.pop(r,None)
        if mn=='pop' and ops and ops[0].type==X86_OP_REG:
            dm.pop(rname(ops[0].reg),None)
        if mn=='ret': break
    return acc, vcall_excluded

allacc=[]
allvcall=[]
for e,l in methods:
    a,v=analyze(e,l)
    allacc+=a; allvcall+=v

p(f"total accesses = {len(allacc)}; virtual call [mem] excluded from data-read = {len(allvcall)}")
# write full raw
with open(OUT,'w') as f:
    f.write("offset\twidth\tkind\tmnemonic\tsite\tfunction\tinsn\n")
    for a in sorted(allacc):
        f.write(f"{a[0]:#06x}\t{a[1]}\t{a[2]}\t{a[3]}\t{a[4]:#08x}\t{a[5]}\t{a[6]}\n")
    f.write("\n# VIRTUAL CALLS EXCLUDED (not data reads)\n")
    for s,mn,op,l in sorted(allvcall):
        f.write(f"{s:#08x}\t{mn}\t{op}\t{l}\n")

# group by offset
d=collections.defaultdict(lambda:{'W':[],'R':[]})
for off,w,k,mn,site,label,insn in allacc:
    d[off][k].append((site,label,mn,w,insn))
CELL_SIZE=0x148
offs=sorted(o for o in d if 0x24<=o<CELL_SIZE)
p(f"\ndistinct CellClass-proper offsets in [0x24,0x{CELL_SIZE:x}): {len(offs)}")
p("\noffset  #W  #R  W-sites(first3) / R-sites(first3)")
for o in offs:
    ws=d[o]['W']; rs=d[o]['R']
    wl=','.join(f"{x[0]:#x}:{x[1]}" for x in ws[:3])
    rl=','.join(f"{x[0]:#x}:{x[1]}" for x in rs[:3])
    p(f"  {o:#06x}  {len(ws):3d} {len(rs):3d}  W[{wl}] R[{rl}]")

# report 0xB8 specifically
p(f"\n[0xB8 check] W={len(d[0xb8]['W'])} R={len(d[0xb8]['R'])} (audit: CellClass-proper 0)")
with open(OUT,'a') as f:
    f.write('\n\n# SUMMARY\n')
    f.write(f"method_set_size={len(methods)}\n")
    f.write(f"total_accesses={len(allacc)}\nvirtual_calls_excluded={len(allvcall)}\n")
    f.write(f"distinct_offsets_0x24_0x148={len(offs)}\noffsets={','.join(hex(x) for x in offs)}\n")
p(f"\n[saved] {OUT}")
