# -*- coding: utf-8 -*-
"""R211 c9：记录级判别谓词机械搜索。
数据集：每个 (类 c, BCA(c) 中一条非零 mdisp 记录 r)，标签 L = (r.mdisp ∈ V(c))。
候选谓词（逐字段与组合）逐个评估「能否完全区分 L=1 与 L=0」，报告混淆矩阵。
最后给出胜出谓词，并订正律 W。
"""
import sys,struct,collections,json,itertools
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(addr=base+4*i,sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
TDOWN=set(v['pTD'] for v in own.values())
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a].keys())-{0} for a in VS}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(a=b,pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
rows=[]
for a in sorted(V):
    for b in BCA[a]:
        r=rec(b)
        if r['mdisp']==0: continue
        r2=dict(r); r2['cls']=a; r2['L']=1 if r['mdisp'] in V[a] else 0
        r2['tdown']= r['pTD'] in TDOWN
        rows.append(r2)
print('记录级样本 = %d ; L=1 %d ; L=0 %d'%(len(rows),sum(r['L'] for r in rows),sum(1 for r in rows if r['L']==0)))
def evalpred(name,f):
    tp=sum(1 for r in rows if r['L']==1 and f(r))
    fp=sum(1 for r in rows if r['L']==0 and f(r))
    fn=sum(1 for r in rows if r['L']==1 and not f(r))
    tn=sum(1 for r in rows if r['L']==0 and not f(r))
    ok = (fn==0 and fp==0)
    print('%-46s %s  TP=%-5d FN=%-4d FP=%-4d TN=%-4d'%(name,'PERFECT' if ok else '       ',tp,fn,fp,tn))
    return ok
cands=[
 ('pdisp == -1',lambda r:r['pdisp']==-1),
 ('pdisp != -1',lambda r:r['pdisp']!=-1),
 ('vdisp == 0',lambda r:r['vdisp']==0),
 ('nc == 0',lambda r:r['nc']==0),
 ('nc == -1',lambda r:r['nc']==-1),
 ('attr == 0',lambda r:r['attr']==0),
 ('pTD ∈ TD_OWN',lambda r:r['tdown']),
 ('mdisp == 4',lambda r:r['mdisp']==4),
 ('pdisp==-1 ∧ attr==0',lambda r:r['pdisp']==-1 and r['attr']==0),
 ('pdisp==-1 ∧ nc==0',lambda r:r['pdisp']==-1 and r['nc']==0),
 ('tdown ∨ mdisp==4',lambda r:r['tdown'] or r['mdisp']==4),
 ('tdown ∧ mdisp!=4',lambda r:r['tdown'] and r['mdisp']!=4),
 ('nc>=1',lambda r:r['nc']>=1),
 ('nc>=0',lambda r:r['nc']>=0),
 ('(nc>=1) ∨ (nc==-1 ∧ pdisp==-1)',lambda r:r['nc']>=1 or (r['nc']==-1 and r['pdisp']==-1)),
]
print()
best=[]
for n,f in cands:
    if evalpred(n,f): best.append(n)
# 特征交叉：mdisp 值 × L
print('\n=== mdisp 值 → L 分布 ===')
tab=collections.defaultdict(lambda:[0,0])
for r in rows: tab[r['mdisp']][r['L']]+=1
for m in sorted(tab): print('  mdisp=%-7d L1=%-5d L0=%-5d'%(m,tab[m][1],tab[m][0]))
print('\n=== 对 mdisp=4 且 L=1 的记录，看 pdisp/vdisp/nc 分布 ===')
for lbl,pred in (('L=1',lambda r:r['L']==1),('L=0',lambda r:r['L']==0)):
    sub=[r for r in rows if pred(r) and r['mdisp']==4]
    print(' %s & mdisp=4 : n=%d'%(lbl,len(sub)))
    for k in ('pdisp','vdisp','nc','attr','tdown'):
        print('    %-7s %s'%(k,collections.Counter(r[k] for r in sub).most_common(6)))
print('\n=== L=0 记录的全部特征（26 条预期）===')
for r in rows:
    if r['L']==0:
        print('  cls=%#010x mdisp=%-6d pTD=%#010x tdown=%-5s nc=%-3d pdisp=%-3d vdisp=%-3d attr=%#x'%(
            r['cls'],r['mdisp'],r['pTD'],r['tdown'],r['nc'],r['pdisp'],r['vdisp'],r['attr']))
json.dump({'n':len(rows),'L1':sum(r['L'] for r in rows),'L0':sum(1 for r in rows if r['L']==0),
  'perfect':best,
  'mdisp_tab':{str(m):[tab[m][1],tab[m][0]] for m in sorted(tab)}},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c9.json','w'),indent=1)
