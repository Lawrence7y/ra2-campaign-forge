
import json,collections,math
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
rows=json.load(open(OUT/'work'/'rows.json'))
step0=json.load(open(OUT/'work'/'step0.json'))
M=step0['metrics']
SUBS=[f'S{i:02d}' for i in range(1,22)]
print('SUBS with rows:', sorted({r['sub'] for r in rows}))
print('rows total', len(rows))
# 口径1 仅RTTI
mat={}
for s in SUBS:
    xs=[r for r in rows if r['sub']==s]
    A=sum(1 for r in xs if r['has2_rtti'] and r['has4'])
    B=sum(1 for r in xs if r['has2_rtti'] and not r['has4'])
    C=sum(1 for r in xs if not r['has2_rtti'] and r['has4'])
    D=sum(1 for r in xs if not r['has2_rtti'] and not r['has4'])
    mat[s]=dict(A=A,B=B,C=C,D=D,n=len(xs))
tot={k:sum(mat[s][k] for s in SUBS) for k in 'ABCDn'}
print('=== 口径1 仅 RTTI ===')
for s in SUBS:
    v=mat[s]; print(f"{s} n={v['n']:4d} A={v['A']:3d} B={v['B']:4d} C={v['C']:3d} D={v['D']:4d}  check={v['A']+v['B']+v['C']+v['D']==v['n']}")
print('TOTAL', tot)
# YRpp
yc=[r for r in rows if r['yrpp_conf']]
print('rows with yrpp_conf computed', len(yc), 'ok', sum(1 for r in yc if r['yrpp_conf']['ok']))
print('  of those has4 too:', sum(1 for r in yc if r['yrpp_conf']['ok'] and r['has4']))
print('  ok & no has4:', sum(1 for r in yc if r['yrpp_conf']['ok'] and not r['has4']))
print('  bindings among all rows:', sum(1 for r in rows if r['yrpp']))
json.dump(dict(mat=mat,tot=tot), open(OUT/'work'/'matrix1.json','w'), indent=1)
