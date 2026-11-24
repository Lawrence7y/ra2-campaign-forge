"""③b base rate for S13 pool, seed 20261119, 2000 trials, sample 8.
D-42-faithful detectors (same operationalization as S05_KPROVED3 for cross-card comparability):
  strict = jump-table(①) OR falsifiable-errcode(②) OR memshape(③) OR full-io-loop(④)
  loose  = strict OR D-42细则#1 guard chain (>=3 mutually-exclusive gates, distinct targets)
Each ④ loop must have inside its body: explicit write + boundary cmp + pointer/index advance.
Extent source: SURVEY_RING24 classification.tsv ext_lo/ext_hi (self-written CFG extent, NOT atlas).
Reports both the full S13 static-inference pool (126) and the 47-row candidate pool.
Card S13-KPROVED2.
"""
import os, sys, json, csv, random
sys.path.insert(0, os.path.dirname(__file__))
from s13lib import MD, DATA, va2off, disasm_range

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_KPROVED2"
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
poolfile = json.load(open(BASE + r'\work\pool.json', encoding='utf-8'))

# extents from survey CFG
ext = {}
for r in csv.DictReader(open(CLS, encoding='utf-8'), delimiter='\t'):
    try:
        ext[r['entry']] = (int(r['ext_lo'],16), int(r['ext_hi'],16))
    except Exception:
        pass

def get_insns(entry):
    if entry not in ext:
        return []
    lo,hi = ext[entry]
    return disasm_range(lo,hi)

# ---- D-42 faithful detectors (verbatim operationalization of S05_KPROVED3) ----
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
    addrs=[i.address for i in ins]; idx={a:k for k,a in enumerate(addrs)}
    for k,i in enumerate(ins):
        if not (i.mnemonic.startswith('j') and i.mnemonic!='jmp'): continue
        try: t=int(i.op_str,16)
        except ValueError: continue
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
            except ValueError: pass
    return len(tgts)>=3 and len(set(tgts))>=3

def detect(entry, tier):
    ins=get_insns(entry)
    if not ins: return False,{}
    jt=has_jumptable(ins); er=has_errcode(ins); ms=has_memshape(ins); io=has_full_io_loop(ins)
    gc=has_guard_chain(ins)
    strict=jt or er or ms or io
    res=(strict or gc) if tier=='loose' else strict
    return res,dict(jt=jt,err=er,memshape=ms,ioloop=io,guardchain=gc,n=len(ins))

# pool definitions
static_pool = sorted([r['entry'] for r in poolfile['candidates']] )  # placeholder, rebuilt below
# full S13 static-inference pool from coverage (126)
s13static=[]
with open(COV,encoding='utf-8') as f:
    f.readline()
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=8 and p[1]=='S13' and p[4]=='[静态推断]':
            s13static.append(p[0])
cand_pool = sorted([r['entry'] for r in poolfile['candidates']])

def measure(pool_entries, label):
    pool=[e for e in pool_entries if e in ext]
    out={}
    for tier in ('strict','loose'):
        passing=[]
        feats={}
        for e in pool:
            ok,ft=detect(e,tier)
            feats[e]=ft
            if ok: passing.append(e)
        N=len(pool); K=len(passing); p=K/N; E8=8*p
        rnd=random.Random(20261119); trials=2000; hits=0; pset=set(passing)
        for _ in range(trials):
            samp=rnd.sample(pool,8)
            hits+=sum(1 for e in samp if e in pset)
        mc=hits/trials
        out[tier]=dict(N=N,K=K,p=p,E8=E8,mc_mean=mc,passing=sorted(passing),
                       note='K=N*p and E[8]=8*p are identities, not a check (M3/§8.7判据3)')
        print('[%s][%s] N=%d K=%d p=%.6f E[8]=%.6f MC=%.6f'%(label,tier,N,K,p,E8,mc))
    return dict(label=label, pool=pool, tiers=out,
                features={e:feats for e in feats})

res = {
 's13_static_pool_126': measure(s13static, 's13_static_126'),
 'candidate_pool_47': measure(cand_pool, 'candidate_47'),
}

json.dump(res, open(BASE + r'\EVIDENCE\baselines.json','w',encoding='utf-8'), indent=2)
print('wrote EVIDENCE/baselines.json')
