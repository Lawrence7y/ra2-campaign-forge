#!/usr/bin/env python3
"""R170 F：F24 语料值「失效期标注」的逐次限定测量（R161 曾记「限定集中一处而非逐次」）。"""
import json, re
ROOT='/home/t628/projects/ra2-campaign-forge'
V=ROOT+'/lead/next_re_20261117_r14/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
rows={}
for p in open(V,encoding='utf-8',newline='').read().split('\n')[1:]:
    if not p.strip(): continue
    f=p.split('\t'); rows[f[0]]=f
s=rows['F24'][1]
QUAL=('11-22','快照','失效','不是现盘','现盘','相对')
occ=[m.start() for m in re.finditer('4,417',s)]
res=[]
for o in occ:
    w200=s[max(0,o-100):o+100]
    res.append((o,[k for k in QUAL if k in w200]))
    print('@%d quals=%s'%(o,[k for k in QUAL if k in w200]))
print('occurrences',len(occ))
covered=[o for o,q in res if q]
print('with-qualifier-in-+-100:',len(covered),'of',len(occ))
# 反控：距离到最近限定词
def nearest(o):
    best=None
    for k in ('11-22','快照','失效','不是现盘'):
        for m in re.finditer(re.escape(k),s):
            d=abs(m.start()-o)
            best=d if best is None or d<best else best
    return best
print('nearest-qualifier-distances',[nearest(o) for o in occ])
json.dump({'occ':occ,'with':covered,'dist':[nearest(o) for o in occ]},open(ROOT+'/_r170/r170f_f24loc.json','w'),ensure_ascii=False,indent=1)
