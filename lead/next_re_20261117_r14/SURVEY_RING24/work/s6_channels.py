
import json,collections
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
rows=json.load(open(OUT/'work'/'rows.json'))
A=[r for r in rows if r['has2_rtti'] and r['has4']]
print('A',len(A))
def ch(r):
    if r['n_direct'] and r['n_livevt']: return 'both'
    if r['n_direct']: return 'direct'
    if r['n_livevt']: return 'livevt'
    return 'none'
c=collections.Counter(ch(r) for r in A)
print('A by ring4 channel', dict(c))
print()
print('A direct-only sample:')
for r in [x for x in A if ch(x)=='direct'][:12]:
    print('  ',r['entry'],r['sub'],'cls',r['rtti_cls'],'slot',r['rtti_slot'],'ndir',r['n_direct'],r['name'][:40])
print('A livevt-only sample:')
for r in [x for x in A if ch(x)=='livevt'][:12]:
    print('  ',r['entry'],r['sub'],'cls',r['rtti_cls'],'slot',r['rtti_slot'],'nlv',r['n_livevt'],r['name'][:40])
print()
# per subsystem channel split
for s in [f'S{i:02d}' for i in range(1,22)]:
    xs=[r for r in A if r['sub']==s]
    print(s, 'A=',len(xs), dict(collections.Counter(ch(r) for r in xs)))
