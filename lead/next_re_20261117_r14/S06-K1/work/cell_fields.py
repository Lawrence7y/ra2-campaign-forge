"""
Scan CellClass methods (vtable slots + ctor/dtor + known users) for field accesses.
Uses function_atlas for method bounds. Tracks registers holding `this` (CellClass*).
Records (disp, width, read/write, site, function).
"""
from pehelp import *
import struct, collections

ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas = {}
with open(ATLAS) as f:
    next(f)
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2:
            atlas[int(p[0],16)] = int(p[1])

VT_CELL = 0x7e4eec
# primary vtable methods: read slots that are .text addresses
methods=[]
for i in range(0,60):
    f=u32(VT_CELL+i*4)
    if not f: continue
    s=section_of(f)
    if s and s[4]=='.text': methods.append((f, f'vt_slot{i}'))
# add ctor/dtor and known users
methods += [(0x47bbf0,'ctor'),(0x47bb60,'dtor'),(0x483a00,'ctor2?'),
            (0x485020,'ore_value'),(0x47ff80,'getcenter'),
            (0x5683c0,'attach'),(0x5687f0,'detach'),
            (0x47e8a0,'link_add_inner'),(0x47ea90,'link_del_inner')]

def fn_end(entry):
    sz=atlas.get(entry)
    if sz: return entry+sz
    return None

def analyze(entry, label, maxb=0x800):
    end=fn_end(entry)
    if end is None or (end-entry)>maxb: end=entry+maxb
    nbytes=end-entry
    insns=disasm(entry, nbytes)
    # dataflow: set of regs holding this
    thisregs={'ecx'}
    acc=[]
    for ins in insns:
        mn=ins.mnemonic
        ops=ins.operands
        # mov reg, reg  /  lea reg,[reg]  propagation
        if mn in ('mov','lea','push') and ops:
            dst=ops[0]; src=ops[1] if len(ops)>1 else None
            if mn=='mov' and dst.type==X86_OP_REG and src and src.type==X86_OP_REG:
                if src.reg in thisregs: thisregs.add(dst.reg)
                else: thisregs.discard(dst.reg)
            if mn=='lea' and dst.type==X86_OP_REG and src and src.type==X86_OP_MEM:
                if src.mem.base in thisregs: thisregs.discard(dst.reg) # field addr, not this
        # memory operand access
        for op in ops:
            if op.type==X86_OP_MEM and op.mem.base in thisregs:
                disp=op.mem.disp
                if disp<0: continue
                width=op.size
                acc.append((disp, width, mn, ins.address, label))
        # clobber on call (caller-saved) - conservative: keep esi/edi/ebx/ebp, drop eax/ecx/edx
        if mn=='call':
            for r in ('eax','ecx','edx'): thisregs.discard(r)
        if mn in ('pop',) and ops and ops[0].type==X86_OP_REG:
            thisregs.discard(ops[0].reg)
        if mn=='ret': break
    return acc

allacc=[]
for entry,label in methods:
    allacc += analyze(entry,label)

# condense by disp: writers (mov) vs readers
bydisp=collections.defaultdict(lambda:{'w':[],'r':[]})
for disp,width,mn,site,label in allacc:
    if mn in ('mov','movzx','movsx') and False:
        pass
    # classify by whether mem operand is dst (write) - need re-check; here approximate via ins id not stored
    bydisp[disp]['r'].append((width,mn,site,label))  # placeholder; refined below

print(f"scanned {len(methods)} methods, {len(allacc)} accesses")
print("NOTE: this is a coarse scan; see EVIDENCE/field_access_raw.txt for full rows")
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K1\EVIDENCE\field_access_raw.txt","w") as f:
    for disp,width,mn,site,label in sorted(allacc):
        f.write(f"{disp:#06x}\t{width}\t{mn}\t{site:#08x}\t{label}\n")
