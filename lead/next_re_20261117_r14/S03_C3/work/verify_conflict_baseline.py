
import os,json,random,csv
BASE=r'D:\Project\ra2-campaign-forge'
OUT=BASE+r'\lead\next_re_20261117_r14\S03_C3\EVIDENCE'
targets=['0065CAC0','004324B0','00552490','006C9890','00631CC0','0065D150','00431E80']

# ---- ⑱ conflict check by entry address ----
roots=[BASE+r'\docs\re', BASE+r'\re_atlas\kb', BASE+r'\lead\GOAL_THREE_TARGETS_20261018.md', BASE+r'\lead\next_re_20261117_r14\COVERAGE']
scanfiles=[]
for root in roots:
    if os.path.isfile(root): scanfiles.append(root)
    elif os.path.isdir(root):
        for dp,dn,fn in os.walk(root):
            for f in fn: scanfiles.append(os.path.join(dp,f))
conflicts=[]
for p in scanfiles:
    try:
        with open(p,encoding='utf-8',errors='replace') as f:
            for i,line in enumerate(f,1):
                for t in targets:
                    if t in line.upper() or ('0x'+t) in line.lower():
                        conflicts.append(dict(entry=t,file=p.replace(BASE,''),line=i,text=line.strip()[:200]))
    except: pass
json.dump(conflicts,open(OUT+r'\conflict18.json','w'),indent=1,ensure_ascii=False)
from collections import Counter
c=Counter(x['entry'] for x in conflicts)
print('CONFLICT18 total hits',len(conflicts),'by entry',dict(c))
for x in conflicts[:30]: print('  ',x['entry'],x['file'],x['line'],x['text'][:120])

# ---- random baseline (same subsystem, same # rows) ----
rows=json.load(open(BASE+r'\lead\next_re_20261117_r14\S03_CRITERION\EVIDENCE\rows.json',encoding='utf-8'))
# atlas subset
atlas=[r for r in rows if r.get('in_atlas')]
print('S03 rows total',len(rows),'atlas',len(atlas))
from collections import Counter
print('grade dist atlas',Counter(r['grade'] for r in atlas))
# baseline space B = [静态推断] rows (108)
B=[r for r in atlas if r['grade']=='[静态推断]']
B_direct=[r for r in B if r.get('n_direct',0)>0]
B_rtti_direct=[r for r in B if r.get('n_direct',0)>0 and r.get('n_rtti',0)>0]
print('space B n=',len(B),' with direct=',len(B_direct),' with rtti+direct=',len(B_rtti_direct))
# space all atlas
A_direct_rtti=[r for r in atlas if r.get('n_direct',0)>0 and r.get('n_rtti',0)>0]
print('all atlas with direct+rtti',len(A_direct_rtti),'/',len(atlas))

def monte(pop, k, seeds=10, seed0=1000):
    res={}
    for s in range(seeds):
        rng=random.Random(seed0+s)
        samp=rng.sample(pop,k)
        res[s]=sum(1 for r in samp if r.get('n_direct',0)>0 and r.get('n_rtti',0)>0)
    return res
# baseline: sample k=7 from [静态推断] 108 rows, criterion = has direct call + rtti (①②④)
resB=monte(B,7,10,1000)
# baseline: sample k=7 from all 194 atlas rows
resA=monte(atlas,7,10,2000)
baseB=len(B_rtti_direct)/len(B); baseA=len(A_direct_rtti)/len(atlas)
out=dict(space_B_n=len(B),space_B_qual=len(B_rtti_direct),baseB=baseB,E7_B=7*baseB,seeds_B=resB,mean_B=sum(resB.values())/10,
         space_A_n=len(atlas),space_A_qual=len(A_direct_rtti),baseA=baseA,E7_A=7*baseA,seeds_A=resA,mean_A=sum(resA.values())/10,
         method='sampling without replacement, 10 seeds, criterion=n_direct>0 and n_rtti>0 (ring 2+4), same subsystem S03, k=7 rows')
json.dump(out,open(OUT+r'\random_baseline.json','w'),indent=1)
print('BASELINE B base=',baseB,'E7=',7*baseB,'seeds',list(resB.values()),'mean',out['mean_B'])
print('BASELINE A base=',baseA,'E7=',7*baseA,'seeds',list(resA.values()),'mean',out['mean_A'])
