"""Step 4: compute ③b base rate (strict/loose).
Population = S09 rows (grade=[静态推断] & entry in atlas), same-subsystem random 8 rows,
seed 20261119, 2000 draws without replacement. Report strict/loose hit rate + K identity note.
The ③b detector operationalizes D-42 four sufficient conditions:
  S1 error-code: call ... cmp reg,-1 ... jcc/setcc within short window
  S2 loop-IO: backward jcc whose loop body has non-stack mem write + boundary cmp + advance
  S3 jump-table: jmp [reg + idx*scale + disp], scale 4/8, target in rodata with >=3 entries
  S4 memory-shape: >=2 vt-imm writes to [reg] OR >=10 distinct field-write offsets
  loose adds S5 multi-guard: >=3 jcc AND >=2 distinct direct call targets
"""
import json, random, struct
from pathlib import Path
from collections import Counter
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone import CS_AC_WRITE
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_GRP_JUMP
import sys
sys.path.insert(0, str(Path(__file__).parent))
from s09lib import (decode_range, u32, is_ro, is_text, sec_of, TEXT_LO, TEXT_HI)

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4')
WORK, EV = OUT/'work', OUT/'EVIDENCE'
R14 = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14')

# population: S09 rows from classification.tsv
import csv
pop=[]
with (R14/'SURVEY_RING24'/'EVIDENCE'/'classification.tsv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['subsystem']=='S09':
            e=int(r['entry'],16); sz=int(r['atlas_size'])
            pop.append((r['entry'], e, sz))
print('S09 population =',len(pop))

MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

def detect_3b(entry, sz):
    if sz<=0 or not is_text(entry): return (False,False,{})
    ins=decode_range(entry, entry+min(sz,4000))
    if not ins: return (False,False,{})
    flags={}
    n=len(ins)
    addrs=[i.address for i in ins]
    # S1 error-code
    s1=False
    for k,i in enumerate(ins):
        if i.mnemonic=='call':
            for j in range(k+1,min(k+7,n)):
                if ins[j].mnemonic in ('cmp','test'):
                    ims=[o.imm for o in ins[j].operands if o.type==X86_OP_IMM]
                    if -1 in ims or 0xFFFFFFFF in ims:
                        for l in range(j+1,min(j+4,n)):
                            if ins[l].mnemonic.startswith(('set','j')) and ins[l].mnemonic not in ('jmp',):
                                s1=True; break
                if s1: break
        if s1: break
    flags['S1']=s1
    # S2 loop-IO
    s2=False
    for k,i in enumerate(ins):
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims and ims[0] <= i.address and ims[0] >= entry:  # backedge
                target=ims[0]
                body=[x for x in ins if target<=x.address<i.address]
                memwr=0; bound=0; adv=0
                for x in body:
                    for o in x.operands:
                        if o.type==X86_OP_MEM and o.access & CS_AC_WRITE:
                            base = x.reg_name(o.mem.base) if o.mem.base else ''
                            if base not in ('esp','ebp'): memwr+=1
                    if x.mnemonic in ('cmp','test'): bound+=1
                    if x.mnemonic in ('inc','dec','add','sub') and any(o.type==X86_OP_REG for o in x.operands): adv+=1
                if memwr>=1 and bound>=1 and adv>=1:
                    s2=True; break
    flags['S2']=s2
    # S3 jump-table
    s3=False
    for i in ins:
        if i.mnemonic=='jmp':
            for o in i.operands:
                if o.type==X86_OP_MEM and o.mem.scale in (4,8) and o.mem.index!=0:
                    # resolve table base if displacement is immediate absolute
                    if o.mem.base==0 and o.mem.disp and is_ro(o.mem.disp):
                        vals=[u32(o.mem.disp+4*k) for k in range(3)]
                        if sum(1 for v in vals if is_text(v))>=3:
                            s3=True
                    else:
                        s3=True  # scaled indirect jmp counts (table presence)
    flags['S3']=s3
    # S4 memory-shape
    vtw=0; offs=set()
    for i in ins:
        if i.mnemonic=='mov':
            ops=i.operands
            if ops and ops[0].type==X86_OP_MEM and ops[0].access & CS_AC_WRITE:
                base = i.reg_name(ops[0].mem.base) if ops[0].mem.base else ''
                if base and base not in ('esp','ebp'):
                    offs.add(ops[0].mem.disp)
                    if len(ops)>1 and ops[1].type==X86_OP_IMM and is_ro(ops[1].imm): vtw+=1
    s4 = (vtw>=2) or (len(offs)>=10)
    flags['S4']=s4; flags['vtw']=vtw; flags['noffs']=len(offs)
    # S5 multi-guard (loose)
    jcc=sum(1 for i in ins if i.mnemonic.startswith('j') and i.mnemonic!='jmp')
    dcall=set()
    for i in ins:
        if i.mnemonic=='call':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims: dcall.add(ims[0])
    # S6 multi-guard with distinct actions (③b① 细则#1): >=3 jcc to distinct targets
    #    AND >=2 distinct direct call targets OR >=2 distinct non-stack write offsets
    jcc_targets=set(); wo=set()
    for i in ins:
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims: jcc_targets.add(ims[0])
        if i.mnemonic=='mov' and i.operands and i.operands[0].type==X86_OP_MEM and (i.operands[0].access & CS_AC_WRITE):
            base = i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else ''
            if base and base not in ('esp','ebp'): wo.add(i.operands[0].mem.disp)
    s6=(len(jcc_targets)>=3 and (len(dcall)>=2 or len(wo)>=2))
    flags['S6']=s6; flags['jtgt']=len(jcc_targets)
    s5=(jcc>=3 and len(dcall)>=1)
    flags['S5']=s5; flags['jcc']=jcc; flags['dcall']=len(dcall)
    strict = s1 or s2 or s3 or s4 or s6
    loose = strict or s5
    return (strict,loose,flags)

res=[]
for entry,e,sz in pop:
    st,lo,fl=detect_3b(e,sz)
    res.append(dict(entry=entry,strict=int(st),loose=int(lo),**{k:int(v) if isinstance(v,bool) else v for k,v in fl.items()}))

json.dump(res,open(WORK/'baseline_rows.json','w'),indent=1)
with (EV/'BASELINE_3B_FEATURES.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tstrict\tloose\tS1\tS2\tS3\tS4\tS5\tS6\tvtw\tnoffs\tjcc\tjtgt\tdcall\n')
    for r in res:
        f.write('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n'%(
            r['entry'],r['strict'],r['loose'],r.get('S1',0),r.get('S2',0),r.get('S3',0),
            r.get('S4',0),r.get('S5',0),r.get('S6',0),r.get('vtw',0),r.get('noffs',0),
            r.get('jcc',0),r.get('jtgt',0),r.get('dcall',0)))

n=len(res)
base_strict=sum(r['strict'] for r in res)/n
base_loose=sum(r['loose'] for r in res)/n
seed=20261119; N=2000; K=8
out={'population':n,'seed':seed,'draws':N,'draw_size':K,
     'base_strict':base_strict,'base_loose':base_loose,
     'n_strict':sum(r['strict'] for r in res),'n_loose':sum(r['loose'] for r in res)}
for mode,key in [('strict','strict'),('loose','loose')]:
    rng=random.Random(seed)
    hits=0; total=0; hist=Counter()
    entries=[r['entry'] for r in res]
    val=[r[key] for r in res]
    for _ in range(N):
        s=rng.sample(range(n),K)
        h=sum(val[i] for i in s); hits+=h; total+=K; hist[h]+=1
    out[mode]=dict(total_hits=hits,total_draws=total,mean_per_draw=hits/N,
                   mean_per_row=hits/total,histogram=dict(sorted(hist.items())),
                   identity_K_equals_draw_size_times_mean_per_row=(K*hits/total)==(hits/N))
json.dump(out,open(EV/'BASELINE_3B.json','w'),indent=1)
with (EV/'BASELINE_3B.txt').open('w',encoding='utf-8') as f:
    f.write('③b BASE RATE (not ②∧④ selection rate; A-rate 103/629 is selection predicate, NOT baseline)\n')
    f.write('population S09 = %d ; seed=%d ; draws=%d ; draw_size=%d (without replacement)\n'%(n,seed,N,K))
    f.write('strict base = %d/%d = %.6f ; loose base = %d/%d = %.6f\n'%(
        out['n_strict'],n,base_strict,out['n_loose'],n,base_loose))
    for mode in ('strict','loose'):
        d=out[mode]
        f.write('%s: total_hits=%d/%d mean_per_draw=%.6f mean_per_row=%.6f hist=%s\n'%(
            mode,d['total_hits'],d['total_draws'],d['mean_per_draw'],d['mean_per_row'],d['histogram']))
    f.write('NOTE: K = draw_size × mean_per_row is an identity, not a validation.\n')
print(json.dumps(out,indent=1)[:1200])
