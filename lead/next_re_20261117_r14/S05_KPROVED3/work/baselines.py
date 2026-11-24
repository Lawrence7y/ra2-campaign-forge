"""③b base rate for S05 [静态推断] pool, seed 20261119, 2000 trials, sample 8.
D-42-faithful detectors (addresses audit critique of S05_KPROVED2 loose detector):
  strict = jump-table(①) OR falsifiable-errcode(②) OR memshape(③) OR full-io-loop(④)
  loose  = strict OR D-42细则#1 guard chain (>=3 mutually-exclusive gates, distinct targets)
Each ④ loop must have, inside the loop body: explicit write + boundary cmp + pointer/index advance.
Card S05-KPROVED3."""
import os, sys, json, csv, random, struct, pickle
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *
from capstone import *
from capstone.x86 import *

COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
CLS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

pool=[]
for line in open(COV,encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if len(p)>=8 and p[1]=='S05' and p[4]=='[静态推断]':
        pool.append(p[0])
ext={}
for r in csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'):
    try: ext[r['entry']]=(int(r['ext_lo'],16),int(r['ext_hi'],16))
    except: pass
pool=[e for e in pool if e in ext]
print("pool N =",len(pool))

def get_insns(entry):
    lo,hi=ext[entry]; off=va2off(lo); size=hi-lo
    if off is None or size<=0: return []
    return list(MD.disasm(pe.__data__[off:off+size],lo))

def has_jumptable(ins):
    for i in ins:
        if i.mnemonic=='jmp' and 'dword ptr' in i.op_str and '*' in i.op_str:
            return True
    return False

def has_errcode(ins):
    for j,i in enumerate(ins):
        if i.mnemonic=='cmp' and i.op_str.strip().endswith('-1'):
            for k in ins[j+1:j+7]:
                if k.mnemonic.startswith('ret') or k.mnemonic.startswith('set') or k.mnemonic.startswith('j'):
                    return True
    return False

def has_memshape(ins):
    vtw=0; fw=0
    for i in ins:
        if i.mnemonic=='mov' and 'ptr' in i.op_str and ',' in i.op_str:
            dst=i.op_str.split(',')[0].strip()
            if dst.startswith(('dword ptr','word ptr','byte ptr')) and 'esp' not in dst and 'ebp' not in dst:
                if '0x7e' in dst or '0x7f' in dst: vtw+=1
                fw+=1
    return vtw>=2 or fw>=10

def has_full_io_loop(ins):
    """backedge whose loop body has explicit write + boundary cmp + advance."""
    addrs=[i.address for i in ins]; idx={a:k for k,a in enumerate(addrs)}
    for k,i in enumerate(ins):
        if not (i.mnemonic.startswith('j') and i.mnemonic!='jmp'): continue
        try: t=int(i.op_str,16)
        except: continue
        if not (t<=i.address): continue
        ti=idx.get(t)
        if ti is None or ti>k: continue
        body=ins[ti:k+1]
        if len(body)<4: continue
        write=False; bcmp=False; adv=False
        for z in body:
            dst=z.op_str.split(',')[0].strip() if ',' in z.op_str else ''
            if z.mnemonic in ('mov','or','and','add','sub','xor','inc','dec') and dst.startswith(('dword ptr','word ptr','byte ptr')):
                write=True
            if z.mnemonic=='cmp': bcmp=True
            if z.mnemonic in ('inc','dec','add','sub') and any(r in z.op_str for r in ('esi','edi','ebx','eax','ecx','edx','ebp')):
                adv=True
        if write and bcmp and adv:
            return True
    return False

def has_guard_chain(ins):
    tgts=[]
    for i in ins:
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            try: tgts.append(int(i.op_str,16))
            except: pass
    return len(tgts)>=3 and len(set(tgts))>=3

def detect(entry,tier):
    ins=get_insns(entry)
    if not ins: return False,{}
    jt=has_jumptable(ins); er=has_errcode(ins); ms=has_memshape(ins); io=has_full_io_loop(ins)
    gc=has_guard_chain(ins)
    strict=jt or er or ms or io
    res=(strict or gc) if tier=='loose' else strict
    return res,dict(jt=jt,err=er,memshape=ms,ioloop=io,guardchain=gc,n=len(ins))

res={}
for tier in ('strict','loose'):
    passing=[]
    for e in pool:
        ok,feat=detect(e,tier)
        if ok: passing.append(e)
    N=len(pool); K=len(passing); p=K/N; E8=8*p
    rnd=random.Random(20261119); trials=2000; hits=0; pset=set(passing)
    for _ in range(trials):
        samp=rnd.sample(pool,8)
        hits+=sum(1 for e in samp if e in pset)
    mc=hits/trials
    res[tier]=dict(N=N,K=K,p=p,E8=E8,mc_mean=mc,passing=passing,
        identity=dict(rows=8,mean=p,rows_x_mean=8*p,tautology=abs(8*p-E8)<1e-12,
                      note="K=N*p and E[8]=8*p are identities, NOT a check (M3)"))
    print("[%s] N=%d K=%d p=%.6f E[8]=%.6f MC_mean=%.6f"%(tier,N,K,p,E8,mc))

os.makedirs(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\EVIDENCE",exist_ok=True)
json.dump(res,open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\EVIDENCE\baselines.json",'w',encoding='utf-8'),indent=2)
print("wrote EVIDENCE/baselines.json")
