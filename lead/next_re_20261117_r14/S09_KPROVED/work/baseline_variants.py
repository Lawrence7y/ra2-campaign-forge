#!/usr/bin/env python3
"""Baseline sensitivity: (a) ④=has4 only vs A-set(②∧④); (b) add guard-chain ③b pattern.
Also verify ① entry alignment and ④ sites for the 8 rows. Reads EVIDENCE/pool_3b_flags.tsv.
"""
import csv, random, os
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\EVIDENCE'
CLASS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
rows=list(csv.DictReader(open(CLASS,encoding='utf-8'),delimiter='\t'))
s09=[r for r in rows if r['subsystem']=='S09']
flags={x['entry']:x for x in csv.DictReader(open(os.path.join(EV,'pool_3b_flags.tsv'),encoding='utf-8'),delimiter='\t')}

def mc(pred,label):
    ent=[r['entry'] for r in s09 if pred(r)]
    # count hits among pool
    K=sum(1 for r in s09 if pred(r) and flags[r['entry']]['hit']=='1')
    N=len(s09); p=K/N
    rng=random.Random(20261119); hs=[]
    allent=[r['entry'] for r in s09]
    hitflag={r['entry']:(1 if (pred(r) and flags[r['entry']]['hit']=='1') else 0) for r in s09}
    for _ in range(2000):
        hs.append(sum(hitflag[e] for e in rng.sample(allent,8)))
    print(f'{label}: K={K} N={N} p={p:.4f} analytic8p={8*p:.4f} emp={sum(hs)/2000:.4f}')

mc(lambda r: r['has4_strict']=='1', '④=has4_strict(129) ∧ ③b-proxy')
mc(lambda r: r['has4_strict']=='1' and r['has2_rtti']=='1', 'A-set(②∧④=103) ∧ ③b-proxy')

# ① entry alignment for the 8
for e in ['004AAE90','005BDF70','006A5310','004AB9B0','0063FEA0','006A7780','004ACE70','006ABD30']:
    v=int(e,16)
    print(f'① {e}: 16B-aligned={(v%16==0)} mod16=0x{v%16:X}')
