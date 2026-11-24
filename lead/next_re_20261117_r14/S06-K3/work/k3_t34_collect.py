"""S06-K3 T3+T4 raw data collection (single pass).
T3: MapClass vtable 30 slots + semantics, +0x13C field, scroll origin write counts, GetSize.
T4: 0x485020 call sites, ore type DynamicVector table, RTTI class name, +0xB8 writes, overlay chain.
Outputs separate TSV/TXT under EVIDENCE/.
"""
from lib import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections, bisect, os

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE"
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"

cov = {}
with open(COV, encoding='utf-8') as f:
    next(f)
    for ln in f:
        q=ln.rstrip('\n').split('\t')
        if len(q)>=5:
            cov[q[0].upper()]=(q[1],q[2],q[3],q[4])

asrt=sorted(atlas.items()); keys=[k for k,v in asrt]
def func_of(a):
    i=bisect.bisect_right(keys,a)-1
    if i>=0:
        e,sz=asrt[i]
        if e<=a<e+sz: return (e,sz)
    return None

# ============ T3: MapClass vtable 30 slots ============
VT=0x7ED404
out=[]
out.append("=== T3 MapClass vtable 0x7ED404 (30 slots) ===")
for i in range(30):
    f=u32(VT+i*4)
    if f is None:
        out.append(f"[{i:2d}] <unreadable>"); continue
    c=cov.get(f"{f:08X}")
    sem=c[2] if c else '(not in coverage)'
    nm=c[1] if c else '?'
    out.append(f"[{i:2d}] {f:#010x} size={atlas.get(f,'?')} name={nm} sem={sem}")
marker=u32(VT+30*4)
out.append(f"terminator[30] = {marker:#x} (expected 0x7ED47C)")
with open(os.path.join(EV,'k3_t3_mapslots.txt'),'w',encoding='utf-8') as fh: fh.write('\n'.join(out)+'\n')
print('\n'.join(out))

# ============ T3: scroll origin 0x886FA0/0x886FA4 whole-image access ============
tlo,thi=text_bounds()
code=read(tlo,thi-tlo)
SCROLL={0x886FA0:'scrollX',0x886FA4:'scrollY'}
acc=collections.defaultdict(list)
for ins in md.disasm(code,tlo):
    if ins.id==0: continue
    for idx,op in enumerate(ins.operands):
        if op.type!=X86_OP_MEM: continue
        m=op.mem
        if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID and m.disp in SCROLL:
            kind='write' if (idx==0 and ins.mnemonic in ('mov','add','sub','inc','dec','and','or','xor')) else 'read'
            acc[(SCROLL[m.disp],kind)].append((ins.address,ins.mnemonic,ins.op_str))
out2=["=== T3 scroll origin whole-image accesses (absolute addressing) ==="]
for key in [('scrollX','write'),('scrollX','read'),('scrollY','write'),('scrollY','read')]:
    lst=acc.get(key,[])
    out2.append(f"{key[0]} {key[1]}: {len(lst)}")
    for a,mn,ops in lst[:20]: out2.append(f"   {a:#x}  {mn} {ops}")
with open(os.path.join(EV,'k3_t3_scroll.txt'),'w',encoding='utf-8') as fh: fh.write('\n'.join(out2)+'\n')
print('\n'.join(out2))

# ============ T3: MapClass +0x13C pointer field (0x87F924) writes/reads ============
out3=["=== T3 dword[0x87F924] (MapClass+0x13C) accesses whole-image ==="]
w=[];r=[]
for ins in md.disasm(code,tlo):
    if ins.id==0: continue
    for idx,op in enumerate(ins.operands):
        if op.type!=X86_OP_MEM: continue
        m=op.mem
        if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID and m.disp==0x87F924:
            kind='write' if (idx==0 and ins.mnemonic in ('mov','add','sub','inc','dec','and','or','xor')) else 'read'
            (w if kind=='write' else r).append((ins.address,ins.mnemonic,ins.op_str))
out3.append(f"writes={len(w)} reads={len(r)}")
for a,mn,ops in w[:20]: out3.append(f"  W {a:#x} {mn} {ops}")
for a,mn,ops in r[:10]: out3.append(f"  R {a:#x} {mn} {ops}")
with open(os.path.join(EV,'k3_t3_87f924.txt'),'w',encoding='utf-8') as fh: fh.write('\n'.join(out3)+'\n')
print('\n'.join(out3))

# ============ T4: 0x485020 call sites (direct E8) ============
GCA_ORE=0x485020
sites=[]
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==GCA_ORE:
        sites.append(va)
out4=["=== T4 direct call sites of 0x485020 (ore value) ==="]
out4.append(f"count={len(sites)}")
for s in sites:
    out4.append(f"  {s:#x}  caller_func={func_of(s)}")
with open(os.path.join(EV,'k3_t4_ore_calls.txt'),'w',encoding='utf-8') as fh: fh.write('\n'.join(out4)+'\n')
print('\n'.join(out4))

# ============ T4: ore type table ============
out5=["=== T4 ore type table DynamicVectorClass<TiberiumClass*> ==="]
out5.append(f"vftable @0x7F56BC = {u32(0x7F56BC):#x}")
out5.append("--- static init function 0x721640 (first 60 insns) ---")
for ins in disasm(0x721640,0x120,60):
    if ins.id==0: continue
    out5.append(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
with open(os.path.join(EV,'k3_t4_ore_table.txt'),'w',encoding='utf-8') as fh: fh.write('\n'.join(out5)+'\n')
print('\n'.join(out5))

# ============ T4: RTTI of 0x7F56BC ============
out6=["=== T4 RTTI for 0x7F56BC (scan COL around) ==="]
for cand in [0x7F56B0,0x7F56B4,0x7F56B8,0x7F56C0,0x7F56C4]:
    col=u32(cand)
    td=u32(col+0xC) if col and section_of(col) else None
    name=None
    if td and section_of(td):
        np=u32(td+8)
        if np and section_of(np):
            b=read(np,64); name=b.split(b'\0')[0].decode('latin1','replace')
    out6.append(f"  cand {cand:#x}: COL={col and hex(col)} TD={td and hex(td)} name={name}")
with open(os.path.join(EV,'k3_t4_ore_rtti.txt'),'w',encoding='utf-8') as fh: fh.write('\n'.join(out6)+'\n')
print('\n'.join(out6))
print("\n[saved T3/T4 evidence files]")
