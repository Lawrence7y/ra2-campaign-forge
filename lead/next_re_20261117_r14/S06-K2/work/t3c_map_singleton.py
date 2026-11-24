"""T3c: isolate MapClass-singleton writes to +0x13c and dimension init, using atlas function intervals."""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections, bisect
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t3c_map_singleton.txt"
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
starts=sorted(atlas)
def func_of(va):
    i=bisect.bisect_right(starts,va)-1
    if i<0: return None
    s=starts[i]; sz=atlas.get(s,0)
    if s<=va<s+max(sz,1) and sz<=0x8000: return s
    return None
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg','fstp','stosd','rep'}
SINGLE=0x87f7e8
tlo,thi=text_bounds(); data=pe.get_data(SECTIONS[0][2],SECTIONS[0][3])

# find instructions that load singleton into a reg (mov reg,0x87f7e8) -> map site to func
sing_load_funcs=collections.defaultdict(list)
w13c_funcs=collections.defaultdict(list)
dim_funcs=collections.defaultdict(list)
for ins in md.disasm(data,tlo):
    if ins.id==0: continue
    mn=ins.mnemonic; ops=ins.operands
    f=func_of(ins.address)
    if mn=='mov' and len(ops)>=2 and ops[1].type==X86_OP_IMM and ops[1].imm==SINGLE and ops[0].type==X86_OP_REG:
        if f: sing_load_funcs[f].append(ins.address)
    for idx,op in enumerate(ops):
        if op.type!=X86_OP_MEM or op.mem.base==0: continue
        d=op.mem.disp
        if d==0x13c and idx==0 and mn in WRITEMN and f:
            w13c_funcs[f].append(ins.address)
        if d in (0x14c,0x150,0x154) and f:
            dim_funcs[f].append((ins.address,d,'W' if (idx==0 and mn in WRITEMN) else 'R',f"{mn} {ins.op_str}"))

p("Functions that BOTH load singleton 0x87f7e8 AND write [reg+0x13c]:")
both=set(sing_load_funcs)&set(w13c_funcs)
for f in sorted(both):
    p(f"  fn {f:#x} (size {atlas.get(f)}): singleton-loads={[hex(x) for x in sing_load_funcs[f][:4]]}, +0x13c-writes={[hex(x) for x in w13c_funcs[f][:6]]}")
    for a,d,k,insn in dim_funcs.get(f,[])[:12]:
        p(f"      dim +{d:#x} {k} {a:#x}: {insn}")

p("\nFunctions with singleton load AND dimension field access:")
for f in sorted(set(sing_load_funcs)&set(dim_funcs)):
    p(f"  fn {f:#x} (size {atlas.get(f)}): dims={[(hex(a),hex(d),k,i) for a,d,k,i in dim_funcs[f][:10]]}")

# Also: find where 512/0x40000 values are written to these fields near singleton funcs
p("\nSearch mov [reg+0x14c/0x150/0x154], imm patterns (base=any):")
for ins in md.disasm(data,tlo):
    if ins.id==0: continue
    mn=ins.mnemonic; ops=ins.operands
    if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_MEM and ops[1].type==X86_OP_IMM:
        d=ops[0].mem.disp
        if d in (0x14c,0x150,0x154):
            f=func_of(ins.address)
            p(f"  {ins.address:#x} fn={f and hex(f)} {mn} {ins.op_str}")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
