"""s7: ③b base rate — strict/loose predicates, seed 20261119, 2000 draws of N=8 from S10 pool."""
import sys, os, json, csv, random
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, sweep_calls, FuncMap, disasm_range
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE=os.path.dirname(__file__); R14=os.path.dirname(os.path.dirname(HERE))
b=Bin(); rtti=build_rtti(b); sw=sweep_calls(b); fm=FuncMap(b,rtti,sw)

def features(ea):
    st,en=fm.extent(ea); insns=disasm_range(b,st,en)
    jt=False; loop_write=False; hresult=False; assert_code=False
    vt_writes=0; field_writes=0
    distinct_acts=set()
    for i,x in enumerate(insns):
        # jump table
        if x.mnemonic=='jmp' and x.operands and x.operands[0].type==X86_OP_MEM and x.operands[0].mem.index:
            jt=True
        # loop w/ explicit non-stack write
        if x.mnemonic.startswith('j') and x.mnemonic!='jmp' and x.operands and x.operands[0].type==X86_OP_IMM:
            tgt=x.operands[0].imm
            if st<=tgt<x.address:
                body=[y for y in insns if tgt<=y.address<=x.address]
                for y in body:
                    if y.mnemonic in ('mov','inc','dec','add','sub','and','or','xor') and y.operands and y.operands[0].type==X86_OP_MEM and '[esp' not in y.op_str and '[ebp' not in y.op_str:
                        loop_write=True
        # HRESULT error code (callee return comparison) vs assert-code push
        if x.mnemonic in ('cmp','test'):
            for o in x.operands:
                if o.type==X86_OP_IMM and (o.imm & 0xffffffff) in (0x80004002,0x80004005,0x80070057):
                    hresult=True
        if x.mnemonic=='push' and x.operands and x.operands[0].type==X86_OP_IMM and (x.operands[0].imm & 0xffffffff) in (0x80004002,0x80004003,0x80004005):
            assert_code=True
        # memory shape
        if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[1].type==X86_OP_IMM and x.operands[0].type==X86_OP_MEM:
            v=x.operands[1].imm
            if b.in_rdata(v): vt_writes+=1
            field_writes+=1
    memshape = (vt_writes>=2 or field_writes>=10)
    strict = jt or loop_write or hresult or memshape
    loose = strict or (assert_code and field_writes>=1)
    return strict,loose

cls=os.path.join(R14,'SURVEY_RING24','EVIDENCE','classification.tsv')
pool=[]
with open(cls,encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        if row.get('subsystem')=='S10':
            pool.append(row['entry'])
print('pool N', len(pool))

counts={'strict':0,'loose':0}
flags={}
for e in pool:
    s,l=features(int(e,16))
    flags[e]={'strict':s,'loose':l}
    counts['strict']+=int(s); counts['loose']+=int(l)
K=len(pool)
p_strict=counts['strict']/K; p_loose=counts['loose']/K
print('K',K,'strict',counts['strict'],f'p={p_strict:.6f}', 'loose',counts['loose'],f'p={p_loose:.6f}')

SEED=20261119; NDRAW=2000; NS=8
random.seed(SEED)
mc={'strict':0.0,'loose':0.0}
for _ in range(NDRAW):
    samp=random.sample(pool,NS)
    mc['strict']+=sum(flags[e]['strict'] for e in samp)
    mc['loose']+=sum(flags[e]['loose'] for e in samp)
mc['strict']/=NDRAW; mc['loose']/=NDRAW
print('MC E[8] strict', f'{mc["strict"]:.4f}', 'loose', f'{mc["loose"]:.4f}')
print('analytic E[8] strict', f'{NS*p_strict:.6f}', 'loose', f'{NS*p_loose:.6f}')
print('K = N*p identity: strict', counts['strict'], '=', f'{K*p_strict:.1f}', ' loose', counts['loose'],'=',f'{K*p_loose:.1f}')

json.dump({'pool':K,'seed':SEED,'ndraw':NDRAW,'nsample':NS,
           'strict':{'K':counts['strict'],'p':p_strict,'E8':NS*p_strict,'MC':mc['strict']},
           'loose':{'K':counts['loose'],'p':p_loose,'E8':NS*p_loose,'MC':mc['loose']},
           'flags':flags},
          open(os.path.join(HERE,'..','EVIDENCE','baseline_3b.json'),'w',encoding='utf-8'),indent=1)
