
import json,collections,math,random
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
rows=json.load(open(OUT/'work'/'rows2.json'))
step0=json.load(open(OUT/'work'/'step0.json')); M=step0['metrics']
SUBS=[f'S{i:02d}' for i in range(1,22)]

def cls2(r, with_yrpp):
    h2 = r['has2_rtti'] or (with_yrpp and r['yrpp_conf'] and r['yrpp_conf']['ok'])
    h4 = r['has4']
    if h2 and h4: return 'A'
    if h2: return 'B'
    if h4: return 'C'
    return 'D'

res={}
for tag,wy in (('RTTI','rtti'),('YRpp','yrpp')):
    mat={}
    for s in SUBS:
        xs=[r for r in rows if r['sub']==s]
        c=collections.Counter(cls2(r, wy=='yrpp') for r in xs)
        mat[s]=dict(n=len(xs), A=c['A'],B=c['B'],C=c['C'],D=c['D'])
    res[tag]=mat

print('=== MATRIX (口径1 仅RTTI) ===')
tot=dict(A=0,B=0,C=0,D=0,n=0)
print('| SUB | n | A | B | C | D | proved | ceil(n/2) | proved+A | 达标? |')
for s in SUBS:
    v=res['RTTI'][s]; m=M[s]
    up=m['proved']+v['A']
    ok= up>=m['threshold']
    for k in tot: tot[k]+=v[k]
    print(f"| {s} | {v['n']} | {v['A']} | {v['B']} | {v['C']} | {v['D']} | {m['proved']} | {m['threshold']} | {up} | {'YES' if ok else 'no'} |")
print('TOTAL', tot)
print()
print('=== 口径2 含YRpp：只影响 C->A ===')
diff={}
for s in SUBS:
    a2=res['YRpp'][s]['A']; a1=res['RTTI'][s]['A']
    if a2!=a1: diff[s]=(a1,a2)
print('subsystems with A change:', diff)
print('A total 口径1', sum(res['RTTI'][s]['A'] for s in SUBS), '口径2', sum(res['YRpp'][s]['A'] for s in SUBS))
# achievability both
for tag in ('RTTI','YRpp'):
    npass=sum(1 for s in SUBS if M[s]['proved']+res[tag][s]['A'] >= M[s]['threshold'])
    print(tag,'achiev', npass, [s for s in SUBS if M[s]['proved']+res[tag][s]['A']>=M[s]['threshold']])
json.dump(res, open(OUT/'work'/'matrix_final.json','w'), indent=1)
