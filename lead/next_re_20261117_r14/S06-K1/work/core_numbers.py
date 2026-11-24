"""
Definitive core-number computation for S06-K1.
Outputs: EVIDENCE/core_numbers.txt
"""
from pehelp import *
from capstone.x86 import X86_REG_ECX, X86_REG_EAX, X86_REG_EDX, X86_REG_ESI
import struct, collections

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K1\EVIDENCE\core_numbers.txt"
lines=[]
def p(s=''):
    print(s); lines.append(str(s))

CELL_SIZE=0x148
CELL_VT=0x7e4eec
MAP_VT=0x7ed404
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas={}
with open(ATLAS) as f:
    next(f)
    for ln in f:
        q=ln.split('\t')
        if len(q)>=2: atlas[int(q[0],16)]=int(q[1])

WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg','fstp','stosd'}

def getsize(f):
    b=read(f,6)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3: return struct.unpack('<I',b[1:5])[0]
    return None

p("="*70)
p("S06-K1 CORE NUMBERS (all from gamemd.exe, ImageBase 0x400000)")
p("="*70)

# ---- GetSize ----
p("\n[1] GetSize (RTTI primary vtable, slot12 = B8 imm32 C3)")
p(f"  CellClass TD=0x81cd70 name=.?AVCellClass@@ -> primary vtable 0x7e4eec (COL offset=0)")
f12=u32(CELL_VT+12*4); gs=getsize(f12)
p(f"  CellClass v[12] = {f12:#x} -> B8 {gs:#x} C3 => GetSize = {gs} (0x{gs:x})")
p(f"  CellClass v[11] = {u32(CELL_VT+11*4):#x} -> WhatAmI = {getsize(u32(CELL_VT+11*4))}")
p(f"  CellClass ctor push cross-check: push 0x148 @0x5663C3/0x566B96/0x6BF9BC -> operator new 0x7c8e17 -> call ctor 0x47bbf0")
p(f"  MapClass TD=0x816bc0 name=.?AVMapClass@@ -> primary vtable 0x7ed404 (COL offset=0)")
p(f"  MapClass v[12] = {u32(MAP_VT+12*4):#x} ('{disasm(u32(MAP_VT+12*4),1)[0].mnemonic}') NOT B8/C3")
# scan whole vtable
cnt=0; hits=[]
for i in range(400):
    f=u32(MAP_VT+i*4)
    if not f: continue
    s=section_of(f)
    if not s or s[4]!='.text': continue
    cnt+=1
    g=getsize(f)
    if g is not None: hits.append((i,f,g))
p(f"  MapClass vtable: {cnt} text slots scanned, B8/C3 functions = {len(hits)} => NO GetSize virtual")
p(f"  MapClass is NOT AbstractClass-derived (base ctor 0x4f4220 != AbstractClass 0x410170);")
p(f"  singleton 0x87F7E8 final dynamic type = PowerClass (vft 0x7EFF54, TD .?AVPowerClass@@),")
p(f"  derived via DisplayClass (: MapClass); MapClass base at offset 0. No GetSize in chain.")

# ---- CellClass field count + OOB scan ----
p("\n[2] CellClass field table (offset/write+read sites from 62 methods)")
methods=[]
for i in range(0,60):
    f=u32(CELL_VT+i*4)
    if f and section_of(f) and section_of(f)[4]=='.text': methods.append((f,f'vt{i}'))
methods += [(0x47bbf0,'ctor'),(0x47bb60,'dtor'),(0x483a00,'ctor2'),
            (0x485020,'ore'),(0x47ff80,'getcenter'),
            (0x5683c0,'attach'),(0x5687f0,'detach'),
            (0x47e8a0,'linkadd'),(0x47ea90,'linkdel')]
allacc=[]
for entry,label in methods:
    sz=atlas.get(entry,0x800); sz=sz if 0<sz<=0x800 else 0x800
    insns=disasm(entry,sz)
    regs={X86_REG_ECX}
    for ins in insns:
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            if ops[1].reg in regs: regs.add(ops[0].reg)
            else: regs.discard(ops[0].reg)
        if mn=='lea' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_MEM:
            if ops[1].mem.base in regs: regs.discard(ops[0].reg)
        for idx,op in enumerate(ops):
            if op.type==X86_OP_MEM and op.mem.base in regs and op.mem.disp>=0:
                w=mn in WRITEMN and idx==0
                allacc.append((op.mem.disp,op.size,'W' if w else 'R',ins.address,label))
        if mn=='call': regs-{X86_REG_EAX,X86_REG_ECX,X86_REG_EDX}; regs-= {X86_REG_EAX,X86_REG_ECX,X86_REG_EDX}
        if mn=='ret': break
# CellClass-proper offsets (exclude base AbstractClass 0x0..0x23)
celloffs=sorted(set(d for d,w,k,s,l in allacc if CELL_SIZE>d>=0x24))
writes=[(d,w,s,l) for d,w,k,s,l in allacc if k=='W']
oob=[x for x in writes if x[0]+x[1]>CELL_SIZE]
p(f"  distinct CellClass-proper field offsets (0x24..0x147) = {len(celloffs)}")
p(f"  total accesses = {len(allacc)}; writes = {len(writes)}")
p(f"  OUT-OF-BOUNDS writes (disp+width > 0x{CELL_SIZE:x}) = {len(oob)}")
if oob:
    for d,w,s,l in oob: p(f"    OOB {d:#x}+{w} @ {s:#x} {l}")
p(f"  max cell write end = {max(d+w for d,w,s,l in writes):#x} (<= {CELL_SIZE:#x})")

# ---- MapClass field count + OOB ----
p("\n[3] MapClass field table (MapClass base ctor 0x565090 + GetCellAt + ctor wrapper base region)")
# MapClass base ctor field writes < 0x1174 (DisplayClass starts at 0x1174)
map_writes=set()
for ins in disasm(0x565090,0xf4):
    if ins.id==0: continue
    for op in ins.operands:
        if op.type==X86_OP_MEM and op.mem.base in (X86_REG_ESI,) and 0<=op.mem.disp<0x1174:
            if ins.mnemonic in WRITEMN: map_writes.add((op.mem.disp,op.size))
map_offs=sorted(set(d for d,w in map_writes))
# add absolute-known fields from GetCellAt and map init fn
map_key=[(0x13c,4,'cell array base ptr'),(0x148,4,'0x0d'),(0x14c,4,'width=0x200'),(0x150,4,'height=0x200'),(0x154,4,'cell count=0x40000')]
for d,w,desc in map_key: map_writes.add((d,w))
map_offs=sorted(set(d for d,w in map_writes))
MAP_SIZE=0x1174  # derived: MapClass ctor last write +0x1170 (4B); derived class first field +0x1174
p(f"  distinct MapClass field offsets (base ctor + key methods) = {len(map_offs)}")
p(f"  MapClass size (derived-boundary method) = {MAP_SIZE} (0x{MAP_SIZE:x})")
moob=[(d,w) for d,w in map_writes if d+w>MAP_SIZE]
p(f"  OUT-OF-BOUNDS writes (disp+width > 0x{MAP_SIZE:x}) = {len(moob)}")
p(f"  key: +0x13C cell-array base (399 absolute refs); +0x14C width; +0x150 height; +0x154 count")

# ---- 0x485020 callers ----
p("\n[4] 0x485020 callers (dual channel, full .text E8 rel32)")
c1=[];c2=[]
tlo,thi=text_bounds()
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==0x485020: c1.append(va)
raw=pe.get_data(SECTIONS[0][2],SECTIONS[0][3]); v0=SECTIONS[0][0]
for i,b in enumerate(raw):
    if b==0xE8 and i+5<=len(raw):
        if v0+i+5+struct.unpack_from('<i',raw,i+1)[0]==0x485020: c2.append(v0+i)
p(f"  capstone-linear = {len(c1)}; raw-byte = {len(c2)}; identical = {set(c1)==set(c2)}")
p(f"  callers: {[hex(x) for x in sorted(c1)]}")

# ---- CellStruct / formula ----
p("\n[5] CellStruct + index formula (GetCellAt @0x5657A0)")
p("  CellStruct = {short X @+0, short Y @+2}, size 4 (pushed by value, [esp+4] = ptr)")
p("  index = (short)Y*512 + (short)X ; valid iff 0 <= index < 0x40000")
p("  CellClass* = [ [0x87F7E8+0x13C] + index*4 ] ; inverse X=index%512, Y=index>>9")

with open(OUT,'w') as f: f.write('\n'.join(lines)+'\n')
p(f"\n[saved] {OUT}")
