"""
S06-K2 T1 FINAL: definitive CellClass field table.
Merges:
  - writes: this-tracked from 50 CellClass methods + rep stosd fills (NO lea)
  - reads:  from t1_reads_complete (no early-ret truncation, no lea, no virtual calls)
Adds derived semantics from ctor values + readPoint context.
Outputs EVIDENCE/t1_FINAL.txt (full) + LAYOUT-ready summary.
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections, re

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_FINAL.txt"
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

# authoritative 63 offsets
OFFSETS=[0x24,0x26,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,
0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,0x11c,
0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140]
assert len(OFFSETS)==63

WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','sar',
         'imul','neg','not','xchg','fstp','fst','fistp','stosd','stosb','stosw'}

def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'
def fn_end(entry,maxb=0x1000):
    sz=atlas.get(entry); return entry+(sz if sz and 0<sz<=maxb else maxb)

CELL_VTS=[0x7e4ec0,0x7e4ec8,0x7e4ed0,0x7e4eec]
methods=[]; seen=set()
for vt in CELL_VTS:
    for i in range(40):
        f=u32(vt+i*4)
        if f and section_of(f) and section_of(f)[4]=='.text' and f not in seen:
            seen.add(f); methods.append((f,f'vt{vt:x}[{i}]'))
for f,l in [(0x47bbf0,'ctor'),(0x47bb60,'dtor'),(0x483a00,'ctor2'),(0x485020,'ore'),
            (0x47ff80,'getcenter'),(0x5683c0,'attach'),(0x5687f0,'detach'),
            (0x47e8a0,'linkadd'),(0x47ea90,'linkdel')]:
    if f not in seen: methods.append((f,l))

# ---- WRITE scan (no early ret break, skip lea, handle rep stosd separately) ----
writes=collections.defaultdict(list)
for e,label in methods:
    dm={'ecx':0}; pending={}
    insns=disasm(e,fn_end(e)-e)
    for ins in insns:
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rname(ops[1].reg); d=rname(ops[0].reg)
            if s in dm: dm[d]=dm[s]
            else: dm.pop(d,None)
        elif mn=='lea' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            d=rname(ops[0].reg); m=ops[1].mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            if b in dm: dm[d]=dm[b]+m.disp
            else: dm.pop(d,None)
        elif mn in ('add','sub') and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM:
            d=rname(ops[0].reg)
            if d in dm: dm[d]+=ops[1].imm if mn=='add' else -ops[1].imm
        # rep stosd write: mem dst is es:[edi], width = ecx*4
        if mn in ('rep','stosd') and 'stosd' in ins.op_str:
            if 'edi' in dm:
                start=dm['edi']
                writes[start].append((ins.address,label,'rep stosd',f'rep stosd [edi]+.. (edi=this+{start:#x})',start,0x30))
        if mn=='lea': continue
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM: continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            b=rname(m.base) if m.base!=X86_REG_INVALID else None
            idxr=rname(m.index) if m.index!=X86_REG_INVALID else None
            eff=None
            if b in dm and idxr is None: eff=dm[b]+m.disp
            elif b in dm and idxr in dm: eff=dm[b]+m.disp+dm[idxr]*m.scale
            if eff is None or eff not in OFFSETS: continue
            if idx==0 and mn in WRITEMN and mn!='stosd':
                w=4
                if 'byte ptr' in ins.op_str: w=1
                elif 'word ptr' in ins.op_str and 'dword ptr' not in ins.op_str: w=2
                writes[eff].append((ins.address,label,mn,f"{ins.mnemonic} {ins.op_str}",eff,w))
        if mn=='call':
            for r in ('eax','ecx','edx'): dm.pop(r,None)

# ---- READ scan from t1_reads_complete evidence ----
reads=collections.defaultdict(list)
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_reads_complete.txt") as f:
    for ln in f:
        if ln.startswith('#') or ln.startswith('offset') or not ln.strip(): continue
        q=ln.rstrip('\n').split('\t')
        if len(q)<5: continue
        try: off=int(q[0],16); site=int(q[1],16)
        except: continue
        reads[off].append((site,q[4],q[2],q[3]))  # site, origin, mn, insn

# ---- coverage: write at O width w covers byte offsets [O,O+w) ----
def wcover(off):
    out=[]
    for ws,lst in writes.items():
        for site,label,mn,insn,start,w in lst:
            if start<=off<start+w: out.append((site,label,mn,insn,start,w))
    return out

# semantic labels derived from ctor + read context + K1/ledger anchors
SEM={
0x24:('MapCoords.X (short), world cell X','已证'),
0x26:('MapCoords.Y (short), world cell Y','已证'),
0x28:('FoggedObjects pointer/list (ctor=0)','静态推断'),
0x2c:('ctor=0; read in cell-adjacent funcs (0x57027d/0x573763)','静态推断'),
0x30:('next pointer in cell object linked list (element +0x30)','已证'),
0x34:('ctor=0; read in dtor 0x47bbc7','静态推断'),
0x38:('TerrainType / LandType (ctor=0xffff=-1)','静态推断'),
0x3c:('ctor=0','未证'),
0x40:('ctor=0','未证'),
0x44:('Overlay/Tiberium type ID (ctor=-1; read by 0x485020 ore value)','已证'),
0x48:('ctor=-1 (overlay subtype/frame?)','静态推断'),
0x4c:('ctor=0','未证'),
0x50:('ctor=-1','未证'),
0x54:('ctor=-1','未证'),
0x58:('ctor=-1','未证'),
0x5c:('ctor=-1','未证'),
0x60:('ctor=-1','未证'),
0x64:('ctor=-1','未证'),
0x68:('first of 4-dword block at +0x68 (0x68/6c/70/74)','静态推断'),
0x6c:('2nd dword of +0x68 block (ctor=0)','静态推断'),
0x70:('3rd dword of +0x68 block (ctor=0)','静态推断'),
0x74:('4th dword of +0x68 block (ctor=0)','静态推断'),
0x78:('ctor=0','未证'),
0x7c:('start of 12-dword zero-fill [0x7c..0xab]','静态推断'),
0xac:('start of 12-dword zero-fill [0xac..0xdb]','静态推断'),
0xdc:('ctor=0','未证'),
0xe0:('ctor=0','未证'),
0xe4:('cell object linked-list HEAD A (list 0)','已证'),
0xe8:('cell object linked-list HEAD B (list 1)','已证'),
0xec:('ctor=0','未证'),
0xf0:('ctor=0','未证'),
0xf4:('ctor=0','未证'),
0xf8:('ctor=0','未证'),
0xfc:('virtual-delete pointer in dtor (0x47bb91); not MapCoords','静态推断'),
0x100:('read in attach/detach wrappers (0x5687c2 etc)','静态推断'),
0x104:('ctor=0x10000','静态推断'),
0x108:('word, ctor=0','未证'),
0x10a:('word, ctor=0x3e8 (1000)','静态推断'),
0x10c:('word, ctor=0x3e8','静态推断'),
0x10e:('word, ctor=0x3e8','静态推断'),
0x110:('word, ctor=0x3e8','静态推断'),
0x112:('word, ctor=0x3e8','静态推断'),
0x114:('word, ctor=0x3e8','静态推断'),
0x116:('word, ctor=0xffff','静态推断'),
0x118:('byte, ctor=0xff','静态推断'),
0x119:('byte, ctor=0','未证'),
0x11a:('byte; read with constants 8/5/0xc/1 (cell flags for passability)','静态推断'),
0x11b:('height level (byte, signed; read via movsx in pathing)','已证'),
0x11c:('byte, ctor=0','未证'),
0x11d:('byte, ctor=0','未证'),
0x11e:('Tiberium density (byte); ore value = typevalue*(density+1)','已证'),
0x11f:('byte, ctor=0','未证'),
0x120:('byte, ctor=0xfe','静态推断'),
0x121:('byte, ctor=0xfe','静态推断'),
0x122:('byte, ctor=0','未证'),
0x124:('byte, ctor=0 (set after other base ctor)','未证'),
0x128:('byte, ctor=0','未证'),
0x12c:('state flags dword; ctor AND ~0x1f; bit3=shroud (per radar doc)','静态推断'),
0x130:('dword, ctor=1','静态推断'),
0x134:('dword, ctor=0','未证'),
0x138:('byte, ctor=0','未证'),
0x13c:('dword; read in attach/detach (0x568483/0x5688b3)','静态推断'),
0x140:('dword; ctor AND 0xff800000; read widely (32 reads)','静态推断'),
}

p("="*72)
p("S06-K2 T1 FINAL CellClass field table (63 fields)")
p("method set 50 (4 CellClass vtables + 9 known); writes: this-track+rep stosd; reads: no-ret-truncation pass; virtual [mem] calls excluded")
p("="*72)
dbl=[]
for off in OFFSETS:
    wc=wcover(off); rc=sorted(set(reads.get(off,[])))
    sem,grade=SEM.get(off,('?','未证'))
    # upgrade grade if double support and known anchor fields
    supp=('YES' if wc and rc else ('Wonly' if wc else ('Ronly' if rc else 'NONE')))
    if supp=='YES': dbl.append(off)
    p(f"{off:#06x} W={len(wc):2d} R={len(rc):2d} {supp:5} [{grade}] {sem}")

p(f"\nDOUBLE-SUPPORT fields (W>=1 AND R>=1) = {len(dbl)}/63")
p("double-support offsets: "+', '.join(hex(x) for x in dbl))
p("0xB8 check: writes=" + str(len(wcover(0xb8))) + " reads=" + str(len(reads.get(0xb8,[]))))

with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
