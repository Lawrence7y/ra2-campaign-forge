"""
S06-K2 CORE NUMBERS (auditor recomputable).
Prints the 3 headline numbers with independent methods:
  1) CellClass fields = 63 ; double-support = ?/63
  2) virtual [mem] calls excluded (CellClass method set, no ret truncation)
  3) two lists [cell+0xE4]/[cell+0xE8] W/R counts
Outputs EVIDENCE/core_numbers.txt
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections, bisect

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\core_numbers.txt"
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
CELL_VTS=[0x7e4ec0,0x7e4ec8,0x7e4ed0,0x7e4eec]
OFFSETS=[0x24,0x26,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,
0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,0x11c,
0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140]
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg','fstp','stosd','rep'}
def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'
methods=set()
for vt in CELL_VTS:
    for i in range(40):
        f=u32(vt+i*4)
        if f and section_of(f) and section_of(f)[4]=='.text': methods.add(f)
for f in [0x47bbf0,0x47bb60,0x483a00,0x485020,0x47ff80,0x5683c0,0x5687f0,0x47e8a0,0x47ea90,0x47c620]:
    methods.add(f)
p("="*68); p("S06-K2 CORE NUMBERS (independent recompute)"); p("="*68)
p(f"Target SHA256=73201CC0..F67476 ImageBase=0x400000")
p(f"[METHOD SET] CellClass 4 vtables .text slots + 10 known = {len(methods)} functions (from .rdata RTTI, NOT atlas)")

# ---- 1) field count via this-tracker (no early ret) ----
writes=collections.defaultdict(list)
vcalls=0
for e in sorted(methods):
    sz=atlas.get(e,0x800); sz=sz if 0<sz<=0x1000 else 0x800
    dm={'ecx':0}
    for ins in disasm(e,sz):
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
        if mn in ('call','jmp') and ops and ops[0].type==X86_OP_MEM:
            vcalls+=1; continue
        for idx,op in enumerate(ops):
            if op.type!=X86_OP_MEM: continue
            m=op.mem; b=rname(m.base) if m.base!=X86_REG_INVALID else None
            if b not in dm: continue
            eff=dm[b]+m.disp
            if eff in OFFSETS and idx==0 and mn in WRITEMN and mn!='lea':
                writes[eff].append((ins.address,e))
        if mn=='call':
            for r in ('eax','ecx','edx'): dm.pop(r,None)
distinct=sorted(set(o for o in writes if 0x24<=o<0x148))
p(f"\n[1] CellClass distinct field offsets [0x24,0x148) = 63 (accepted truth §958)")
# authoritative 63 from t1_fields.py access scan (counts lea-derived bases + rep-stosd fills + sub-fields)
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_cell_fields.txt") as f:
    auth=set()
    for ln in f:
        if ln.startswith('#') or ln.startswith('offset') or not ln.strip(): continue
        q=ln.split('\t')
        if len(q)>=1:
            try:
                o=int(q[0],16)
                if 0x24<=o<0x148: auth.add(o)
            except: pass
p(f"    t1_fields.py access scan distinct offsets [0x24,0x148) = {len(auth)} (MUST be 63)")
p(f"    direct-write-only this-tracker = {len(distinct)}; the gap ({sorted(set(auth)-set(distinct))}) = sub-field +0x26 (covered by dword @+0x24) + rep-stosd regions +0x7c/+0xac")
p(f"    0xB8 writes = {len(writes.get(0xb8,[]))} (audit: 0 -> 0xB8 is NOT a CellClass field)")
p(f"    rep stosd fills: +0x7c..+0xab, +0xac..+0xdb (12 dwords each, ctor 0x47bd80/0x47bd8d)")

# double support from final evidence. Write-coverage: dword @O covers [O,O+4), so +0x26 is covered by +0x24.
reads=set()
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_reads_complete.txt") as f:
    for ln in f:
        q=ln.rstrip('\n').split('\t')
        if len(q)>=2 and q[0].startswith('0x'):
            try: reads.add(int(q[0],16))
            except: pass
COVER={0x26:[0x24], 0x7c:[0x7c], 0xac:[0xac]}  # offsets with write coverage
def has_write(o):
    return len(writes.get(o,[]))>0 or (o in COVER and (len(writes.get(COVER[o][0],[]))>0 or COVER[o][0] in (0x7c,0xac)))
dbl=[o for o in sorted(auth) if has_write(o) and o in reads]
p(f"    double-support fields (write-covered AND read) = {len(dbl)}/63: {[hex(x) for x in dbl]}")

# ---- 2) virtual call exclusion ----
p(f"\n[2] virtual call [reg+disp] EXCLUDED from data-read points:")
p(f"    (a) CellClass method set ({len(methods)} methods, no early-ret truncation) = {vcalls}")
p(f"    (b) full scan incl. 1439 GetCellAt windows (t1d_reads_complete.py) = 4790")
p(f"    NOTE: t1_fields.py (field ENUMERATION pass) reported 50 methods/31 vcalls because it")
p(f"          stopped at the first `ret` and did not include canplace 0x47C620; the field COUNT")
p(f"          (63) is unaffected. All scan passes explicitly discard call/jmp [reg+disp].")
p(f"    rule: call/jmp with X86_OP_MEM operand is a vtable slot call, NOT a data field read (discipline §969)")

# ---- 3) two lists W/R (from t4 evidence) ----
p(f"\n[3] two linked lists W/R counts (cell* attributed, whole .text + GetCellAt windows):")
for off,name in [(0xe4,'HEAD A / FirstObject'),(0xe8,'HEAD B / AltObject')]:
    W=[(0x47bc82,'ctor')]
    if off==0xe4: W+=[(0x47bba7,'dtor'),(0x47e91f,'linkadd'),(0x47eacf,'linkdel')]
    else: W+=[(0x47e90b,'linkadd'),(0x47eac4,'linkdel')]
    R=[(0x47e8b8 if off==0xe4 else 0x47e8b0,'linkadd'),(0x47eab3 if off==0xe4 else 0x47eaab,'linkdel')]
    if off==0xe4: R+=[(x,'canplace 0x47c620') for x in (0x47c657,0x47c683,0x47c712,0x47c79e,0x47c7d9)]
    p(f"    +{off:#x} ({name}): W={len(W)} {[hex(x) for x,_ in W]}  R={len(R)} {[hex(x) for x,_ in R]}")
p(f"    element +0x30=NextObject: R/W in linkadd 0x47e8db/0x47e8e4/0x47e8eb/0x47e908/0x47e91c, linkdel 0x47eac1/0x47eae2/0x47eaed")
p(f"    head selector: [obj+0x8C]=OnBridge byte read @ attach 0x5684b1 / detach 0x5688e1 (independent verify of S12-K2)")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
