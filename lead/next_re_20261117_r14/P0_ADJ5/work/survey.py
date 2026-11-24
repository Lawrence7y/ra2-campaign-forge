#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Survey feature hit-rates over the 1669 not-in-cov addresses + decision logic test."""
import pickle, random, json
from pathlib import Path
from engine import Bin, pred_boundary, prologue, in_text
ROOT=Path(r'D:\Project\ra2-campaign-forge')
WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
idx=pickle.load(open(WD/'idx.pkl','rb'))
calls=idx['calls']; jmps=idx['jmps']; vtgt=idx['vtgt']; sweep=idx['sweep']

addrs=[]
for ln in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8'):
    a=ln.strip()
    if a: addrs.append(int(a,16))
addrs=sorted(set(addrs))
print('not-in-cov count', len(addrs))

bin_=Bin()

def features(va):
    a_call = va in calls
    a_jmp  = va in jmps
    b_vt   = va in vtgt
    cb, ce = pred_boundary(bin_, va)
    db, de = prologue(bin_, va)
    return dict(va=va, a_call=a_call, a_jmp=a_jmp, b_vt=b_vt,
                c=cb, c_ev=ce, d=db, d_ev=de)

# survey all 1669
feats=[features(a) for a in addrs]
def rate(key): return sum(1 for f in feats if f[key])/len(feats)*100
print('--- full-pool 1669 feature rates ---')
for k in ('a_call','a_jmp','b_vt','c','d'):
    print(f'  {k}: {rate(k):.1f}%  ({sum(1 for f in feats if f[k])})')
anyab=[f for f in feats if f['a_call'] or f['a_jmp'] or f['b_vt']]
print(f'  any(a|b): {len(anyab)/len(feats)*100:.1f}% ({len(anyab)})')
strong=[f for f in feats if f['a_call'] or f['b_vt']]
print(f'  strong(E8 call | vt): {len(strong)/len(feats)*100:.1f}% ({len(strong)})')

# first 100 by ascending
first100=feats[:100]
print('--- first100 (ascending) feature rates ---')
for k in ('a_call','a_jmp','b_vt','c','d'):
    print(f'  {k}: {sum(1 for f in first100 if f[k])}/100')
print('  first100 first/last:', format(first100[0]['va'],'08X'), format(first100[-1]['va'],'08X'))

# dump feats for all 1669 for reuse
with open(WD/'feats_all.tsv','w',encoding='utf-8') as f:
    f.write('va\ta_call\ta_jmp\tb_vt\tc\tc_ev\td\td_ev\n')
    for x in feats:
        f.write(f"{x['va']:08X}\t{int(x['a_call'])}\t{int(x['a_jmp'])}\t{int(x['b_vt'])}\t{int(x['c'])}\t{x['c_ev']}\t{int(x['d'])}\t{x['d_ev']}\n")
print('wrote feats_all.tsv')
