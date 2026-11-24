"""
S06-K2 T1b: global CellClass* read-point discovery.
Scan the WHOLE .text for functions that obtain a CellClass* from a trusted source
(GetCellAt 0x5657A0 return EAX, InvalidCell 0xABDC50 imm, 0x485020 callers via ecx),
track that pointer through mov/lea, and collect [reg+disp] READ points at the 63 offsets.
This complements t1_fields.py (which tracks `this` inside CellClass methods).
No function_atlas dependency for the scan itself (skipdata linear sweep of .text).
Outputs EVIDENCE/t1_global_reads.txt
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_global_reads.txt"
_lines=[]
def p(s=''):
    print(s); _lines.append(str(s))

CELL_OFFSETS = set(range(0x24,0x80)) | {0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
    0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,
    0x11c,0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140}
GETCELLAT=0x5657A0
INVALIDCELL=0xABDC50
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','sar',
         'imul','neg','not','xchg','fstp','fst','fistp','stosd','stosb','stosw','rep','pop'}

def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'

# Functions that call GetCellAt -> find by linear sweep of call rel32
tlo,thi=text_bounds()
funcs=set()
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)==5:
        tgt=va+5+struct.unpack('<i',b[1:5])[0]
        if tgt==GETCELLAT:
            funcs.add(va)   # site; will analyze windows around it
p(f"GetCellAt direct call sites = {len(funcs)}")

# Instead of per-function, analyze a window around each GetCellAt call site:
# track from the call forward (EAX=cell) up to ~120 instructions.
reads=collections.defaultdict(list)
excluded=0

def analyze_window(site, span_fwd=400):
    global excluded
    # start a bit before the call to catch ecx source too
    start=site
    insns=disasm(start, span_fwd)
    dm={}      # reg -> delta from a cell base (0 = exact CellClass*)
    # EAX becomes a CellClass* right after the GetCellAt call (handled below)
    for ins in insns:
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        # propagation
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rname(ops[1].reg); d=rname(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if ops[1].imm==INVALIDCELL: dm[d]=0
            else: dm.pop(d,None)
        elif mn=='lea' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            d=rname(ops[0].reg); m=ops[1].mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            if b in dm: dm[d]=dm[b]+m.disp
            else: dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if d in dm: dm[d]+=ops[1].imm if mn=='add' else -ops[1].imm
        # After `call 0x5657A0` EAX = CellClass*
        if mn=='call' and ops and ops[0].type==X86_OP_IMM:
            if ops[0].imm==GETCELLAT:
                dm['eax']=0
        # virtual call exclusion
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            excluded+=1
            continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            idxr=rname(m.index) if m.index!=X86_REG_INVALID else None
            eff=None
            if b in dm and idxr is None: eff=dm[b]+m.disp
            elif b in dm and idxr in dm: eff=dm[b]+m.disp+dm[idxr]*m.scale
            if eff is None or eff not in CELL_OFFSETS: continue
            is_write=(idx==0 and mn in WRITEMN)
            reads[eff].append((ins.address,'W' if is_write else 'R',mn,f"{ins.mnemonic} {ins.op_str}"))
        if mn=='call':
            for r in ('eax','ecx','edx'): dm.pop(r,None)
        if mn=='ret': break

for site in sorted(funcs):
    analyze_window(site)

p(f"virtual [mem] calls excluded (windows) = {excluded}")
p(f"\noffset -> #R / #W from GetCellAt-return windows")
byd=collections.defaultdict(lambda:{'R':0,'W':0,'sites':[]})
for off in sorted(reads):
    for site,k,mn,insn in sorted(reads[off]):
        byd[off][k]+=1
        byd[off]['sites'].append((site,k,mn,insn))
for off in sorted(byd):
    r=byd[off]
    p(f"  {off:#06x} R={r['R']} W={r['W']} " + ' | '.join(f"{s:#x}:{k}:{i}" for s,k,m,i in r['sites'][:4]))

with open(OUT,'w') as f:
    f.write("offset\tsite\tkind\tmnemonic\tinsn\n")
    for off in sorted(reads):
        for site,k,mn,insn in sorted(reads[off]):
            f.write(f"{off:#06x}\t{site:#08x}\t{k}\t{mn}\t{insn}\n")
    f.write(f"\n# GetCellAt call sites={len(funcs)} virtual_calls_excluded={excluded}\n")
p(f"\n[saved] {OUT}")
