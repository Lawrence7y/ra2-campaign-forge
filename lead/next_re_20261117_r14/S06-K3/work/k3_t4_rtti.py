"""S06-K3 T4: RTTI with CORRECT chain.
vtable[-1]=COL; COL+0xC=TD; TD+8 = INLINE name char[] (NOT a pointer!).
Fail-closed: report only names actually read.
"""
from lib import *
import struct, re, os, collections

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\EVIDENCE"
out=[]
def cstr(va,maxn=160):
    b=read(va,maxn)
    if not b: return None
    z=b.find(b'\0'); return b[:z if z>=0 else len(b)].decode('latin1','replace')

def classname_of_vtable(vt):
    col=u32(vt-4)
    if not col or not section_of(col): return (col,None,None)
    td=u32(col+0xC)
    if not td or not section_of(td): return (col,td,None)
    nm=cstr(td+8)   # inline char[]
    return (col,td,nm)

out.append("=== RTTI class names (COL=vtable[-1], TD=COL+0xC, name=TD+8 inline) ===")
for vt,label in [(0x7E4EEC,'CellClass main vt'),(0x7E4EC0,'CellClass aux'),(0x7ED404,'MapClass(?)'),
                 (0x7F56BC,'ore table vftable'),(0x7E6060,'LayerClass')]:
    col,td,nm=classname_of_vtable(vt)
    out.append(f"  {label} vt={vt:#x}: COL={col and hex(col)} TD={td and hex(td)} name={nm}")

# Confirm TiberiumClass TD exists, and vector-of-Tiberium name
out.append("\n=== scan all TDs: identify TiberiumClass and vector-of-Tiberium ===")
rdata=next((s for s in SECTIONS if s[4]=='.rdata'),None)
found={}
if rdata:
    v,vs,raw,rs,name=rdata
    data=pe.get_data(raw,rs)
    # TD candidate: u32(td)==vfptr in .rdata and inline char at td+8 starts with '.?A'
    for i in range(0,rs-16,4):
        td=v+i
        vf=u32(td)
        if vf is None or not section_of(vf): continue
        s=cstr(td+8,120)
        if s and (s.startswith('.?AV') or s.startswith('.?AU')):
            found[td]=s
out.append(f"TDs found={len(found)}")
for td,s in sorted(found.items(),key=lambda x:x[1]):
    if 'Tiber' in s or 'Ore' in s or 'Gem' in s:
        out.append(f"  {hex(td)}  {s}")

# Find the COL whose TD is the ore-table TD and print vector template arg.
out.append("\n=== ore table vftable 0x7F56BC detail ===")
col,td,nm=classname_of_vtable(0x7F56BC)
out.append(f"COL={col and hex(col)} TD={td and hex(td)} name={nm}")
# parse template arg
if nm:
    m=re.search(r'DynamicVectorClass@PAV([A-Za-z0-9_]+)@@',nm)
    out.append(f"parsed element class = {m.group(1) if m else '(not simple template)'}")

# +0xB8 writes on TiberiumClass: find all dword writes [reg+0xB8] inside functions that
# reference the ore value function's read of [Tib+0xB8]; conservative: list in .text windows
# around known Tiberium value access sites and INI-parse functions.
out.append("\n=== dword [reg+0xB8] writes whole-image (candidates for Tiberium value field) ===")
tlo,thi=text_bounds(); code=read(tlo,thi-tlo)
b8w=[]; b8r=[]
for ins in md.disasm(code,tlo):
    if ins.id==0: continue
    for idx,op in enumerate(ins.operands):
        if op.type==X86_OP_MEM:
            m=op.mem
            if m.disp==0xB8 and m.base!=X86_REG_INVALID:
                if idx==0 and ins.mnemonic in ('mov','add','sub','inc','dec','and','or','xor','imul'):
                    b8w.append(ins.address)
                else:
                    b8r.append(ins.address)
out.append(f"total [reg+0xB8] writes={len(b8w)} reads={len(b8r)}")
# show writes near 0x485020 read context and near ore table
near=[a for a in b8w if 0x480000<=a<=0x490000 or 0x720000<=a<=0x722000]
out.append(f"writes in ore-value/table-load neighborhood = {len(near)}:")
for a in near[:40]: out.append(f"  W {a:#x}")

with open(os.path.join(EV,'k3_t4_rtti_full.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(out)+'\n')
print('\n'.join(out))
