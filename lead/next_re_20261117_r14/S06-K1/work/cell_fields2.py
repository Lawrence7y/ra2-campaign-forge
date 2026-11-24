"""
CellClass field-access scanner v2: correct read/write classification.
Tracks registers holding `this` (CellClass*). Uses atlas for method bounds.
"""
from pehelp import *
import struct, collections

ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas={}
with open(ATLAS) as f:
    next(f)
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2: atlas[int(p[0],16)]=int(p[1])

VT_CELL=0x7e4eec
methods=[]
for i in range(0,60):
    f=u32(VT_CELL+i*4)
    if not f: continue
    s=section_of(f)
    if s and s[4]=='.text': methods.append((f,f'vt{i}'))
methods += [(0x47bbf0,'ctor'),(0x47bb60,'dtor'),(0x483a00,'ctor2'),
            (0x485020,'ore'),(0x47ff80,'getcenter'),
            (0x5683c0,'attach'),(0x5687f0,'detach'),
            (0x47e8a0,'linkadd'),(0x47ea90,'linkdel')]

def fn_end(entry,maxb=0x800):
    sz=atlas.get(entry)
    return entry+(sz if sz and sz<=maxb else maxb)

def analyze(entry,label):
    end=fn_end(entry)
    insns=disasm(entry,end-entry)
    thisregs={'ecx'}
    acc=[]
    for ins in insns:
        mn=ins.mnemonic; ops=ins.operands
        # propagation
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            if ops[1].reg in thisregs: thisregs.add(ops[0].reg)
            else: thisregs.discard(ops[0].reg)
        if mn=='lea' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            if ops[1].mem.base in thisregs: thisregs.discard(ops[0].reg)
        # access: op0 is dst for mov; for cmp/test both read
        for idx,op in enumerate(ops):
            if op.type==X86_OP_MEM and op.mem.base in thisregs and op.mem.disp>=0:
                is_write = (mn in ('mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg') and idx==0)
                kind='W' if is_write else 'R'
                acc.append((op.mem.disp, op.size, kind, mn, ins.address, label))
        if mn=='call':
            for r in ('eax','ecx','edx'): thisregs.discard(r)
        if mn=='pop' and ops and ops[0].type==X86_OP_REG: thisregs.discard(ops[0].reg)
        if mn=='ret': break
    return acc

allacc=[]
for e,l in methods:
    allacc+=analyze(e,l)

with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K1\EVIDENCE\cell_fields_raw.txt","w") as f:
    f.write("disp\twidth\tkind\tmnemonic\tsite\tfunction\n")
    for a in sorted(allacc):
        f.write(f"{a[0]:#06x}\t{a[1]}\t{a[2]}\t{a[3]}\t{a[4]:#08x}\t{a[5]}\n")

# summary per disp
d=collections.defaultdict(lambda:{'W':set(),'R':set()})
for disp,w,k,mn,site,label in allacc:
    d[disp][k].add((site,label,mn,w))
print(f"methods={len(methods)} accesses={len(allacc)} distinct disp={len(d)}")
print("\ndisp  #W #R  labels(write) / labels(read)")
for disp in sorted(d):
    ws=d[disp]['W']; rs=d[disp]['R']
    wl=','.join(sorted(set(x[1] for x in ws)))[:50]
    rl=','.join(sorted(set(x[1] for x in rs)))[:50]
    print(f"{disp:#06x} {len(ws):3d} {len(rs):3d}  W[{wl}] R[{rl}]")
