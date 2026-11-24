"""T3f: definitive dataflow - find [reg+0x13c] writes where reg holds singleton 0x87f7e8, using atlas function intervals + reg tracking."""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import bisect, collections
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t3f_arraybase_dataflow.txt"
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
WRITEMN={'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','shl','shr','imul','neg','not','xchg','fstp','stosd','rep'}
SINGLE=0x87f7e8
def rname(reg):
    try: return md.reg_name(reg)
    except: return f'r{reg}'
# only functions that raw-reference the singleton immediate (candidate set)
tlo,thi=text_bounds(); data=pe.get_data(SECTIONS[0][2],SECTIONS[0][3])
cand_funcs=set()
pat=__import__('struct').pack('<I',SINGLE)
i=0
while True:
    j=data.find(pat,i)
    if j<0: break
    va=tlo+j
    k=bisect.bisect_right(starts,va)-1
    if k>=0:
        s=starts[k]; sz=atlas.get(s,0)
        if s<=va<s+sz and sz<=0x8000: cand_funcs.add(s)
    i=j+1
p(f"candidate functions referencing singleton immediate: {len(cand_funcs)}")
results=[]
for f in sorted(cand_funcs):
    sz=atlas.get(f,0x800)
    insns=list(disasm(f,sz))
    singregs=set()
    for ins in insns:
        if ins.id==0: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='mov' and len(ops)>=2 and ops[1].type==X86_OP_IMM and ops[1].imm==SINGLE and ops[0].type==X86_OP_REG:
            singregs.add(rname(ops[0].reg))
        # propagate reg->reg
        elif mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            s=rname(ops[1].reg); d=rname(ops[0].reg)
            if s in singregs: singregs.add(d)
        # check [reg+0x13c] write with reg in singregs
        for idx,op in enumerate(ops):
            if op.type==X86_OP_MEM and op.mem.disp==0x13c and op.mem.base!=0:
                b=rname(op.mem.base)
                if b in singregs and idx==0 and mn in WRITEMN:
                    results.append((f,ins.address,mn,f"{ins.mnemonic} {ins.op_str}",b))
p(f"\n[reg+0x13c] WRITES with base holding singleton 0x87f7e8: {len(results)}")
for f,site,mn,insn,b in results:
    p(f"  fn {f:#x} site {site:#x} base={b}: {insn}")
if not results:
    p("  (none found via this dataflow - array base may be set via a pointer variable / different mechanism)")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
