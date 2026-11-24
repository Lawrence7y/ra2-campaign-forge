
import json,collections
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
rows=json.load(open(OUT/'work'/'rows2.json'))
SUBS=[f'S{i:02d}' for i in range(1,22)]
def st(xs):
    n=len(xs)
    A=sum(1 for r in xs if r['has2_rtti'] and r['has4'])
    B=sum(1 for r in xs if r['has2_rtti'] and not r['has4'])
    C=sum(1 for r in xs if (not r['has2_rtti']) and r['has4'])
    D=sum(1 for r in xs if (not r['has2_rtti']) and not r['has4'])
    p2=(A+B)/n if n else 0; p4=(A+C)/n if n else 0
    exp=n*p2*p4
    return dict(n=n,A=A,B=B,C=C,D=D,p2=p2,p4=p4,exp=exp,
                ratio=(A/exp if exp>0 else None),
                cond4_given_2=(A/(A+B) if A+B else None),
                cond2_given_4=(A/(A+C) if A+C else None))
print('sub  n    A    B    C   D   P(2)   P(4)   exp_ind  obs/exp  A/(A+B)  A/(A+C)')
tot=st(rows)
for s in SUBS:
    v=st([r for r in rows if r['sub']==s])
    print(f"{s} {v['n']:4d} {v['A']:4d} {v['B']:4d} {v['C']:4d} {v['D']:3d} {v['p2']*100:5.1f}% {v['p4']*100:5.1f}% {v['exp']:7.1f}  "
          f"{('%.2f'%v['ratio']) if v['ratio'] is not None else '  --'}  "
          f"{('%.1f%%'%(v['cond4_given_2']*100)) if v['cond4_given_2'] is not None else '  --'}  "
          f"{('%.1f%%'%(v['cond2_given_4']*100)) if v['cond2_given_4'] is not None else '  --'}")
print(f"TOTAL {tot['n']} {tot['A']} {tot['B']} {tot['C']} {tot['D']} {tot['p2']*100:.1f}% {tot['p4']*100:.1f}% {tot['exp']:.1f} ratio={tot['ratio']:.3f} "
      f"A/(A+B)={tot['cond4_given_2']*100:.2f}% A/(A+C)={tot['cond2_given_4']*100:.2f}%")
json.dump(tot, open(OUT/'work'/'totals.json','w'), indent=1)
