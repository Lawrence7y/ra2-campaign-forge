
import json,collections
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
idx=json.load(open(OUT/'work'/'index.json'))
installs={int(k,16):v for k,v in idx['installs'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
# distribute: how many distinct vt per global
multi=0; single=0
dist=collections.Counter()
for g,lst in installs.items():
    vs={v for v,s in lst}
    dist[len(vs)]+=1
print('globals by #distinct installed vt:', sorted(dist.items())[:8], '...')
# for each livevt witness, is g single-vt?  and is install before dispatch?
stat=collections.Counter()
for e,wl in livevt.items():
    for g,vt,slot,install_site,disp_site in wl:
        vs={v for v,s in installs.get(g,[])}
        single_ = len(vs)==1
        before = install_site < disp_site
        stat[(single_,before)]+=1
print('livevt witnesses by (single_vt_global, install_before_dispatch):', dict(stat))
# entry-level: does entry survive strict (single-vt global AND install before dispatch)?
strict=set(); loose=set()
for e,wl in livevt.items():
    for g,vt,slot,install_site,disp_site in wl:
        vs={v for v,s in installs.get(g,[])}
        loose.add(e)
        if len(vs)==1 and install_site<disp_site: strict.add(e)
print('livevt entries loose',len(loose),'strict',len(strict))
rows=json.load(open(OUT/'work'/'rows2.json'))
A=[r for r in rows if r['has2_rtti'] and r['has4']]
A_strict=[]
for r in A:
    e=int(r['entry'],16)
    ok = r['n_direct_out']>0 or (e in strict and r['n_livevt']>0)
    if ok: A_strict.append(r)
print('A loose',len(A),'A strict',len(A_strict))
# per subsystem strict
for s in [f'S{i:02d}' for i in range(1,22)]:
    a=sum(1 for r in A if r['sub']==s); b=sum(1 for r in A_strict if r['sub']==s)
    if a or b: print(f'  {s} A_loose={a:3d} A_strict={b:3d}')
json.dump(sorted('%08X'%int(r['entry'],16) for r in A_strict), open(OUT/'work'/'A_strict.json','w'), indent=0)
