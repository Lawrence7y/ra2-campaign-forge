"""
S06-K2 T1d: READ-COMPLETENESS pass for CellClass fields.
Key fix vs t1_fields.py: does NOT stop at the first `ret` (early conditional returns
like 0x485033 in the ore function hid the +0x11E read at 0x48503F).
Scans each CellClass function from entry to atlas-defined end; tracks this-derived
regs (callee-saved persist across early rets); records only genuine memory READS
(skips lea = address computation, skips rep stosd, skips call/jmp [mem] virtual slots).
Also scans the whole .text for cell* from GetCellAt with NO early-ret break.
Outputs EVIDENCE/t1_reads_complete.txt
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_reads_complete.txt"
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

CELL_OFFSETS=set([0x24,0x26,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,
0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,0x11c,
0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140])
GETCELLAT=0x5657A0
INVALIDCELL=0xABDC50
SKIP_MN={'lea','nop','pref'}  # lea computes address, not a memory read

def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'

def fn_end(entry,maxb=0x1000):
    sz=atlas.get(entry)
    return entry+(sz if sz and 0<sz<=maxb else maxb)

def scan(entry, end, seed_reg, seed_delta=0, stop_at_ret=False, label=''):
    """scan a linear region; seed_reg holds cell* (delta 0). Record genuine reads."""
    reads=[]
    vcalls=0
    insns=disasm(entry, end-entry)
    dm={seed_reg:seed_delta}
    for ins in insns:
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rname(ops[1].reg); d=rname(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if ops[1].imm==INVALIDCELL: dm[d]=0
            else: dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if d in dm: dm[d]+=ops[1].imm if mn=='add' else -ops[1].imm
        if mn=='call' and ops and ops[0].type==X86_OP_IMM and ops[0].imm==GETCELLAT:
            dm['eax']=0
        # virtual call exclusion
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            vcalls+=1
            continue
        if mn in SKIP_MN: continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            idxr=rname(m.index) if m.index!=X86_REG_INVALID else None
            eff=None
            if b in dm and idxr is None: eff=dm[b]+m.disp
            elif b in dm and idxr in dm: eff=dm[b]+m.disp+dm[idxr]*m.scale
            if eff is None or eff not in CELL_OFFSETS: continue
            # skip obvious writes (mem is dst of a write mnemonic)
            WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','sar','imul','neg','not','xchg','fstp','fst','fistp','stosd','stosb','stosw'}
            if idx==0 and mn in WRITEMN: continue
            reads.append((eff, ins.address, mn, f"{ins.mnemonic} {ins.op_str}", label))
        if mn=='call':
            for r in ('eax','ecx','edx'): dm.pop(r,None)
        if stop_at_ret and mn=='ret': break
    return reads, vcalls

# ---- pass A: CellClass methods (this=ecx), no ret break ----
CELL_VTS=[0x7e4ec0,0x7e4ec8,0x7e4ed0,0x7e4eec]
methods=[]; seen=set()
for vt in CELL_VTS:
    for i in range(40):
        f=u32(vt+i*4)
        if f and section_of(f) and section_of(f)[4]=='.text' and f not in seen:
            seen.add(f); methods.append(f)
for f in [0x47bbf0,0x47bb60,0x483a00,0x485020,0x47ff80,0x5683c0,0x5687f0,0x47e8a0,0x47ea90]:
    if f not in seen: methods.append(f)

allreads=[]; total_vcalls=0
for e in methods:
    r,v=scan(e, fn_end(e), 'ecx', stop_at_ret=False, label=f'{e:#x}')
    allreads+=r; total_vcalls+=v

# ---- pass B: GetCellAt call sites windows (eax=cell), no ret break ----
tlo,thi=text_bounds()
sites=[]
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==GETCELLAT:
        sites.append(va)
p(f"CellClass methods={len(methods)}; GetCellAt call sites={len(sites)}")
for site in sites:
    r,v=scan(site, site+500, 'eax', stop_at_ret=False, label=f'gca@{site:#x}')
    allreads+=r; total_vcalls+=v
p(f"virtual [mem] calls excluded (both passes) = {total_vcalls}")

# dedupe by (off, site, insn)
seen_r=set(); uniq=[]
for off,site,mn,insn,label in allreads:
    k=(off,site,insn)
    if k in seen_r: continue
    seen_r.add(k); uniq.append((off,site,mn,insn,label))

byd=collections.defaultdict(list)
for off,site,mn,insn,label in uniq:
    byd[off].append((site,mn,insn,label))
p(f"\noffset -> unique read sites (no early-ret truncation)")
for off in sorted(byd):
    p(f"  {off:#06x} R={len(byd[off]):2d} " + ' | '.join(f"{s:#x}:{i}" for s,m,i,l in byd[off][:5]))

with open(OUT,'w') as f:
    f.write("offset\tsite\tmnemonic\tinsn\torigin\n")
    for off in sorted(byd):
        for site,mn,insn,label in sorted(byd[off]):
            f.write(f"{off:#06x}\t{site:#08x}\t{mn}\t{insn}\t{label}\n")
    f.write(f"\n# methods={len(methods)} gca_sites={len(sites)} vcalls_excluded={total_vcalls}\n")
p(f"\n[saved] {OUT}")
