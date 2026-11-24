"""③b BASE RATE (D-42): population = all 629 S09 rows (grade [静态推断] & entry in atlas),
random 8 rows without replacement, seed 20261119, 2000 draws. Report strict/loose base rate.
Same detect_3b (S1-S6) as used for candidate selection. NOT the ②∧④ selection rate.
"""
import json, csv, random
from pathlib import Path
from collections import Counter
import sys
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone import CS_AC_WRITE
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
sys.path.insert(0, str(Path(__file__).parent))
from s09lib import cfg_extent, u32, is_ro, is_text

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED5')
WORK, EV = OUT/'work', OUT/'EVIDENCE'
R14 = OUT.parent
CLASS = R14/'SURVEY_RING24'/'EVIDENCE'/'classification.tsv'

pop=[]
with CLASS.open(encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['subsystem']=='S09':
            pop.append((r['entry'], int(r['entry'],16)))
print('S09 population =', len(pop))

def detect_3b(entry, ins):
    if not ins: return (False,False,0,0)
    n=len(ins)
    s1=False
    for k,i in enumerate(ins):
        if i.mnemonic=='call':
            for j in range(k+1,min(k+7,n)):
                if ins[j].mnemonic in ('cmp','test'):
                    ims=[o.imm for o in ins[j].operands if o.type==X86_OP_IMM]
                    if -1 in ims or 0xFFFFFFFF in ims:
                        for l in range(j+1,min(j+4,n)):
                            if ins[l].mnemonic.startswith(('set','j')) and ins[l].mnemonic!='jmp':
                                s1=True; break
                    if s1: break
            if s1: break
    s2=False
    for k,i in enumerate(ins):
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims and entry<=ims[0]<=i.address:
                target=ims[0]; body=[x for x in ins if target<=x.address<i.address]
                memwr=0; bound=0; adv=0
                for x in body:
                    for o in x.operands:
                        if o.type==X86_OP_MEM and (o.access & CS_AC_WRITE):
                            base=x.reg_name(o.mem.base) if o.mem.base else ''
                            if base not in ('esp','ebp'): memwr+=1
                    if x.mnemonic in ('cmp','test'): bound+=1
                    if x.mnemonic in ('inc','dec','add','sub') and any(o.type==X86_OP_REG for o in x.operands): adv+=1
                if memwr>=1 and bound>=1 and adv>=1: s2=True; break
    s3=False
    for i in ins:
        if i.mnemonic=='jmp':
            for o in i.operands:
                if o.type==X86_OP_MEM and o.mem.scale in (4,8) and o.mem.index!=0: s3=True
    vtw=0; offs=set()
    for i in ins:
        if i.mnemonic=='mov' and i.operands and i.operands[0].type==X86_OP_MEM and (i.operands[0].access & CS_AC_WRITE):
            base=i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else ''
            if base and base not in ('esp','ebp'):
                offs.add(i.operands[0].mem.disp)
                if len(i.operands)>1 and i.operands[1].type==X86_OP_IMM and is_ro(i.operands[1].imm): vtw+=1
    s4=(vtw>=2) or (len(offs)>=10)
    jcc_targets=set(); wo=set(); dcall=set(); jcc=0
    for i in ins:
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            jcc+=1
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims: jcc_targets.add(ims[0])
        if i.mnemonic=='call':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims: dcall.add(ims[0])
        if i.mnemonic=='mov' and i.operands and i.operands[0].type==X86_OP_MEM and (i.operands[0].access & CS_AC_WRITE):
            base=i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else ''
            if base and base not in ('esp','ebp'): wo.add(i.operands[0].mem.disp)
    s6=(len(jcc_targets)>=3 and (len(dcall)>=2 or len(wo)>=2))
    s5=(jcc>=3 and len(dcall)>=1)
    strict=s1 or s2 or s3 or s4 or s6
    loose=strict or s5
    return strict,loose,jcc,len(dcall)

rows=[]
for eh,e in pop:
    _,_,ins,_=cfg_extent(e)
    st,lo,jcc,dc=detect_3b(e,ins)
    rows.append(dict(entry=eh,strict=int(st),loose=int(lo),jcc=jcc,dcall=dc))
json.dump(rows,open(WORK/'baseline_rows.json','w'),indent=1)
with (EV/'BASELINE_3B_FEATURES.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tstrict\tloose\tjcc\tdcall\n')
    for r in rows: f.write('%s\t%d\t%d\t%d\t%d\n'%(r['entry'],r['strict'],r['loose'],r['jcc'],r['dcall']))

n=len(rows)
base_strict=sum(r['strict'] for r in rows)/n
base_loose=sum(r['loose'] for r in rows)/n
seed=20261119; N=2000; K=8
out=dict(population=n,seed=seed,draws=N,draw_size=K,
         n_strict=sum(r['strict'] for r in rows),n_loose=sum(r['loose'] for r in rows),
         base_strict=base_strict,base_loose=base_loose)
for mode,key in [('strict','strict'),('loose','loose')]:
    rng=random.Random(seed); hits=0; total=0; hist=Counter()
    val=[r[key] for r in rows]
    for _ in range(N):
        s=rng.sample(range(n),K)
        h=sum(val[i] for i in s); hits+=h; total+=K; hist[h]+=1
    out[mode]=dict(total_hits=hits,total_draws=total,mean_per_draw=hits/N,
                   mean_per_row=hits/total,histogram=dict(sorted(hist.items())))
json.dump(out,open(EV/'BASELINE_3B.json','w'),indent=1)
with (EV/'BASELINE_3B.txt').open('w',encoding='utf-8') as f:
    f.write('③b BASE RATE (D-42) — NOT ②∧④ selection rate (A=103/629 is selection predicate)\n')
    f.write('population S09 [静态推断]&atlas = %d ; seed=%d ; draws=%d ; draw_size=%d (without replacement)\n'%(n,seed,N,K))
    f.write('strict base = %d/%d = %.6f ; loose base = %d/%d = %.6f\n'%(
        out['n_strict'],n,base_strict,out['n_loose'],n,base_loose))
    for mode in ('strict','loose'):
        d=out[mode]
        f.write('%s: total_hits=%d/%d mean_per_draw=%.6f mean_per_row=%.6f hist=%s\n'%(
            mode,d['total_hits'],d['total_draws'],d['mean_per_draw'],d['mean_per_row'],d['histogram']))
    f.write('NOTE: K = draw_size x mean_per_row is an identity, NOT a validation (M3).\n')
print(json.dumps(out,indent=1)[:1400])
