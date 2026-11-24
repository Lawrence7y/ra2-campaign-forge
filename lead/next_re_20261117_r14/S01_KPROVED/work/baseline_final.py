# -*- coding: utf-8 -*-
"""Correct weak/strong differential + within-subsystem random baseline for S01."""
import json,random,statistics
d=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01_KPROVED\EVIDENCE\scan_main.json"))
signals=d['signals']; direct=d['direct']; weak=d['weak']; strong=d['strong']
unproven=list(signals.keys())
def has_direct(e): return len(direct.get(e,[]))>0
def has_b3_screen(e):
    s=signals[e]
    return s['jt']>=1 or (s['loops']>=1 and s['cond']>=1) or s['cond']>=3
# YRpp-bound unproven entries (from comprehensive scan): only 0069AE90; and it FAILS strict (JMP_STD form, no distinctive declared-member byte match)
YRPP_BOUND=['0069AE90']
VALID_RING2=[]  # none pass strict ②
print('unproven pool n =',len(unproven))
print('weak (④ direct call at instruction boundary) =',len(weak),f'({len(weak)/len(unproven)*100:.1f}%)')
print('strong (④ + ③b mechanical screen) =',len(strong),f'({len(strong)/len(unproven)*100:.1f}%)')
print('weak\\strong difference =',len(set(weak)-set(strong)),sorted(set(weak)-set(strong)))
print('④+③b + valid ② (full 4-ring) =',len(VALID_RING2))
print('  -> 0069AE90 has YRpp JMP_STD binding but ② FAILS strict (JMP_STD != CALL/JMP_THIS; body globals are generic YRpp globals, not distinctive declared members of Game class)')
print('\nRandom baseline (within S01, random sample of same row count, no replacement):')
for k,n in [('weak',len(weak)),('strong',len(strong)),('full',1)]:
    base = {'weak':len(weak)/len(unproven),'strong':len(strong)/len(unproven),'full':0/len(unproven)}[k]
    exp = n*base
    # empirical 200 draws x5 seeds
    rnd=random.Random(20261118); avgs=[]
    for _ in range(5):
        tot=0
        for _ in range(200):
            samp=rnd.sample(unproven,n)
            c=0
            for e in samp:
                if k=='weak' and has_direct(e): c+=1
                elif k=='strong' and has_direct(e) and has_b3_screen(e): c+=1
                elif k=='full' and e in VALID_RING2: c+=1
            tot+=c
        avgs.append(tot/200)
    print(f'  {k}: sample n={n}, expected hits={exp:.2f}, empirical mean hits over 200 draws ={statistics.mean(avgs):.2f} {[round(a,2) for a in avgs]}')
print('\nBase rate of ② channel in S01 unproven pool: YRpp bound =',len(YRPP_BOUND),'/',len(unproven),f'={len(YRPP_BOUND)/len(unproven)*100:.1f}%; RTTI/vtable rows = 2 (00554400,00643E80) but both ③a thin shells.')
