"""Compute ③b base rate over the S10 static-inference pool (seed 20261119, 2000 draws of 8).
Reports strict/core/loose. Runs my own detector from core.py on all classification S10 rows.
"""
import csv, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

HERE=os.path.dirname(os.path.abspath(__file__))
CLS=r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'

def body_hi(c):
    e=int(c['entry'],16); ext=int(c['ext_hi'],16); atlas=int(c['atlas_size'])
    return ext if ext<=e+max(atlas,16)+64 else e+max(atlas,16)

def main():
    pe=core.PE()
    pool=[]
    with open(CLS,encoding='utf-8') as f:
        for c in csv.DictReader(f,delimiter='\t'):
            if c['subsystem']=='S10': pool.append(c)
    print('S10 pool (classification.tsv subsystem=S10) =', len(pool))
    flags={}
    for c in pool:
        e=int(c['entry'],16); hi=body_hi(c)
        strict,coreb,loose,hits,detail=core.detect_3b(pe,e,hi)
        flags[c['entry']]=dict(strict=strict,core=coreb,loose=loose,hits=hits)
    ns=sum(1 for v in flags.values() if v['strict'])
    nc=sum(1 for v in flags.values() if v['core'])
    nl=sum(1 for v in flags.values() if v['loose'])
    print('strict ③b (incl D-42 detail#1 guards) = %d/%d = %.4f'%(ns,len(pool),ns/len(pool)))
    print('core ③b (①②③④ only, no guards)      = %d/%d = %.4f'%(nc,len(pool),nc/len(pool)))
    print('loose D-42(A)                          = %d/%d = %.4f'%(nl,len(pool),nl/len(pool)))
    for k in ('s1_switch','s2_errcode','s3_shape','s4_loop','s1b_guards'):
        print('   %-12s %d'%(k,sum(1 for v in flags.values() if v['hits'][k])))
    entries=sorted(flags)
    rnd=random.Random(20261119); draws=2000
    ms=mc=ml=0
    for _ in range(draws):
        s=rnd.sample(entries,8)
        ms+=sum(1 for x in s if flags[x]['strict'])
        mc+=sum(1 for x in s if flags[x]['core'])
        ml+=sum(1 for x in s if flags[x]['loose'])
    print('\n%d draws of 8 (seed 20261119):'%draws)
    print('strict mean=%.4f (%.2f%%) => base rate %.4f'%(ms/draws,100*ms/draws/8,ms/draws/8))
    print('core   mean=%.4f (%.2f%%) => base rate %.4f'%(mc/draws,100*mc/draws/8,mc/draws/8))
    print('loose  mean=%.4f (%.2f%%) => base rate %.4f'%(ml/draws,100*ml/draws/8,ml/draws/8))
    print('identity K=rows*mean: strict 8*(%.4f)=%.4f ; loose 8*(%.4f)=%.4f (NOT a check)'%(
        ms/draws/8,ms/draws,ml/draws/8,ml/draws))
    import json
    json.dump(dict(pool=len(pool),strict=ns,core=nc,loose=nl,
                   strict_rate=ns/len(pool),core_rate=nc/len(pool),loose_rate=nl/len(pool),
                   draws=draws,seed=20261119,
                   mean_strict=ms/draws,mean_core=mc/draws,mean_loose=ml/draws,
                   rate_strict=ms/draws/8,rate_core=mc/draws/8,rate_loose=ml/draws/8,
                   per_cond={k:sum(1 for v in flags.values() if v['hits'][k]) for k in ('s1_switch','s2_errcode','s3_shape','s4_loop','s1b_guards')}),
              open(os.path.join(HERE,'baseline.json'),'w'),indent=1)

if __name__=='__main__': main()
