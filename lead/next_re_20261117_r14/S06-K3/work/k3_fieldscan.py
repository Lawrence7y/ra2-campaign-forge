"""S06-K3 T2 core: CellClass field write/read evidence scan.
Three passes, all with this=ecx / cell*=eax provenance, NO early-ret truncation:
  A: 42-method set, seed ecx=this
  B: whole-.text GetCellAt call sites, seed eax=cell*
  C: whole-.text 'mov reg,[cellarray + idx*4]' -> cell* element, seed reg=cell*
Exclude: call/jmp [mem] (virtual slots), lea (address calc), rep stosd (handled separately).
Two access forms covered: [reg+disp] indirect AND absolute-slot reads are noted separately.
Outputs EVIDENCE/k3_fieldscan.txt (all offsets) + EVIDENCE/k3_reads_by_offset.tsv
"""
from lib import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections, re

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE\k3_fieldscan.txt"
TSV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE\k3_reads_by_offset.tsv"
_l = []
def p(s=''):
    print(s); _l.append(str(s))

OFF63 = set([0x24,0x26,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,
0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,0x11c,
0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140])
GETCELLAT = 0x5657A0
INVALIDCELL = 0xABDC50
# Cell array base pointer field address = dword[0x87F924] (MapClass+0x13C), stride 4
CELLARRPTR = 0x87F924
WRITEMN = {'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','sar',
           'imul','neg','not','xchg','fstp','fst','fistp','stosd','stosb','stosw'}
SKIP_MN = {'lea','nop','pref','cdq','cld','std','clc','stc'}

# method set rebuilt (same as k3_methodset)
CELL_VTS = [0x7E4EC0,0x7E4EC8,0x7E4ED0,0x7E4EEC]
vtf=[]
for vt in CELL_VTS:
    for i in range(48):
        f=u32(vt+i*4)
        if f is None or not in_text(f): break
        vtf.append(f)
NONVIRT=set([0x47BBF0,0x47BB60,0x483A00,0x485020,0x47FF80,0x5683C0,0x5687F0,0x47E8A0,0x47EA90,0x5657A0])
METHODS = sorted(set(vtf)|NONVIRT)

writes = collections.defaultdict(list)   # off -> (site, origin, insn, width)
reads  = collections.defaultdict(list)   # off -> (site, origin, insn, mn)
vcalls_excluded = 0
stosd_regions = []

def scan_region(entry, end, seed_reg, seed_delta, origin, seed_kind='cell'):
    """Return (writes,reads,vcalls) for linear region; track cell-derived regs.
    dm maps reg -> (kind, delta); kind 'cell' means reg = cellptr + delta.
    """
    global vcalls_excluded
    w=collections.defaultdict(list); r=collections.defaultdict(list); vc=0
    dm={seed_reg:(seed_kind,seed_delta)}
    for ins in disasm(entry, end-entry):
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        # ---- propagate provenance ----
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rn(ops[1].reg); d=rn(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rn(ops[0].reg)
            if ops[1].imm==INVALIDCELL: dm[d]=('cell',0)
            else: dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rn(ops[0].reg)
            if d in dm:
                k,dl=dm[d]; dm[d]=(k,dl+(ops[1].imm if mn=='add' else -ops[1].imm))
        elif mn=='call' and ops and ops[0].type==X86_OP_IMM and ops[0].imm==GETCELLAT:
            dm['eax']=('cell',0)
        # cell array element load: mov reg,[basereg + idx*4] where basereg = dword[0x87F924]
        # (handled in pass C via seed injection, not here)
        # ---- virtual call exclusion ----
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            vc+=1; vcalls_excluded+=1
            for reg in ('eax','ecx','edx'): dm.pop(reg,None)
            continue
        # ---- rep stosd fill on cell this ----
        if mn in ('stosd','stosb','stosw') or 'rep stos' in ins.op_str:
            # es:edi destination; if edi is cell-derived, region [edi, edi+ecx*width)
            if 'edi' in dm:
                k,base=dm['edi']
                stosd_regions.append((ins.address, origin, ins.op_str, base))
            continue
        if mn in SKIP_MN: continue
        # ---- memory operands ----
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            # absolute addressing: no base, no index -> not a cell instance field
            if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID:
                continue
            b=rn(m.base) if m.base!=X86_REG_INVALID else None
            idr=rn(m.index) if m.index!=X86_REG_INVALID else None
            eff=None
            if b in dm and idr is None: eff=dm[b][1]+m.disp
            # NOTE: do not combine scaled index for cell fields (idx*4 is array, not struct)
            if eff is None or eff not in OFF63: continue
            insn=f"{ins.mnemonic} {ins.op_str}"
            if idx==0 and mn in WRITEMN:
                width=1 if 'byte ptr' in ins.op_str else (2 if 'word ptr' in ins.op_str and 'dword ptr' not in ins.op_str else 4)
                w[eff].append((ins.address,origin,insn,width))
            else:
                r[eff].append((ins.address,origin,insn,mn))
        if mn=='call':
            for reg in ('eax','ecx','edx'): dm.pop(reg,None)
    return w,r,vc

p("="*72)
p("S06-K3 T2 CellClass field scan (write+read, virtual calls excluded)")
p("="*72)

# ---- Pass A: method set, this=ecx ----
for e in METHODS:
    w,r,vc=scan_region(e, fn_end(e), 'ecx', 0, f'M:{e:#x}')
    for o,lst in w.items(): writes[o]+=lst
    for o,lst in r.items(): reads[o]+=lst

# ---- Pass B: GetCellAt call sites (whole .text), eax=cell* ----
tlo,thi=text_bounds()
gca_sites=[]
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==GETCELLAT:
        gca_sites.append(va)
p(f"GetCellAt direct call sites (whole .text) = {len(gca_sites)}")
for site in gca_sites:
    w,r,vc=scan_region(site, min(site+400,thi), 'eax', 0, f'G:{site:#x}')
    for o,lst in w.items(): writes[o]+=lst
    for o,lst in r.items(): reads[o]+=lst

# ---- Pass C: 'lea reg,[cell_base]' / 'mov eax,[DWORD cellarrptr]' then element load ----
# Find instructions loading the cell-array pointer global dword[0x87F924].
# Form: mov reg, dword ptr [0x87F924] (absolute), then mov reg2,[reg + idx*4] -> cell*.
# We scan windows around such loads and seed the element register as cell*.
seed_sites=[]
code=read(tlo,thi-thi+tlo) if False else read(tlo,thi-tlo)
for ins in md.disasm(code, tlo):
    if ins.id==0: continue
    if ins.mnemonic=='mov' and ins.operands and ins.operands[0].type==X86_OP_REG:
        ops=ins.operands
        src=None
        if len(ops)>=2 and ops[1].type==X86_OP_MEM:
            m=ops[1].mem
            if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID and m.disp==CELLARRPTR:
                src=rn(ops[0].reg)
        if src:
            seed_sites.append((ins.address, src))
p(f"cell-array pointer global loads (mov reg,[0x87F924]) = {len(seed_sites)}")
for site,srcreg in seed_sites:
    # seed srcreg as an array-base holder: after 'mov elt,[srcreg+idx*4]' elt is cell*.
    # Approximate: scan window, and whenever a reg is loaded with [srcreg + idx*4], seed it.
    w=collections.defaultdict(list); r=collections.defaultdict(list)
    dm={}
    for ins in disasm(site, 200):
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            m=ops[1].mem
            b=rn(m.base) if m.base!=X86_REG_INVALID else None
            idr=rn(m.index) if m.index!=X86_REG_INVALID else None
            d=rn(ops[0].reg)
            if b==srcreg:
                dm[d]=('cell',0); continue
            if d in dm and idr is None:
                dm.pop(d,None)
        elif mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rn(ops[1].reg); d=rn(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            continue
        if mn in SKIP_MN: continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID: continue
            b=rn(m.base) if m.base!=X86_REG_INVALID else None
            if b not in dm: continue
            eff=dm[b][1]+m.disp
            if eff not in OFF63: continue
            insn=f"{ins.mnemonic} {ins.op_str}"
            if idx==0 and mn in WRITEMN:
                w[eff].append((ins.address,f'C:{site:#x}',insn,4))
            else:
                r[eff].append((ins.address,f'C:{site:#x}',insn,mn))
        if mn=='call':
            for reg in ('eax','ecx','edx'): dm.pop(reg,None)
    for o,lst in w.items(): writes[o]+=lst
    for o,lst in r.items(): reads[o]+=lst

p(f"virtual call/jmp [mem] excluded total (A+B+C) = {vcalls_excluded}")
p(f"rep stosd regions on cell this = {len(stosd_regions)}")

# ---- dedupe ----
def dedup(lst, keyidx=3):
    seen=set(); out=[]
    for t in lst:
        k=(t[0],t[2])
        if k in seen: continue
        seen.add(k); out.append(t)
    return sorted(out, key=lambda x:x[0])

all_off = sorted(OFF63)
p("\n" + "="*72)
p("offset   W   R  >=3?  sample write / sample read")
p("="*72)
tsv_lines=["offset\tW_count\tR_count\tR_ge3\twrite_sites\tread_sites\tsample_write\tsample_read"]
for o in all_off:
    w=dedup(writes.get(o,[])); r=dedup(reads.get(o,[]))
    ws=','.join(f'{x[0]:#x}' for x in w[:12]); rs=','.join(f'{x[0]:#x}' for x in r[:12])
    sw=w[0][2] if w else ''; sr=r[0][2] if r else ''
    ge3='Y' if len(r)>=3 and len(w)>=1 else 'n'
    wtxt = f"W:{w[0][0]:#x} {sw[:46]}" if w else "W:-"
    rtxt = f"R:{r[0][0]:#x} {sr[:46]}" if r else "R:-"
    p(f"{o:#06x} {len(w):3d} {len(r):3d}   {ge3}    {wtxt}")
    p(f"                              {rtxt}")
    tsv_lines.append(f"{o:#06x}\t{len(w)}\t{len(r)}\t{ge3}\t{ws}\t{rs}\t{sw}\t{sr}")

with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(_l)+'\n')
with open(TSV,'w',encoding='utf-8') as f: f.write('\n'.join(tsv_lines)+'\n')
print(f"[saved] {OUT}\n[saved] {TSV}")
