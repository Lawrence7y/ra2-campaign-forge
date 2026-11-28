# -*- coding: utf-8 -*-
"""R211 c10：记录级判别谓词定稿。
观察：L=0（extras 26 条）的 pTD 全是 .?AV 类名（StageClass/FlasherClass/BounceClass/
CComObjectRootBase/CComObjectRootEx），且都不在 TD_OWN。
猜想 P1：判别谓词是「pTD 名字以 .?AU 开头（struct/interface）」而不是 .?AV。
一次输出：全部候选谓词的 TP/FN/FP/TN；L=1 与 L=0 记录的 pTD 名字前缀分布；
        以及 L=1 & mdisp=4 的 pTD 名单。"""
import sys,struct,collections,json
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
def tdname(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
rows=[]
for a in sorted(V):
    for b in BCA[a]:
        r=rec(b)
        if r['mdisp']==0: continue
        r['cls']=a; r['L']=1 if r['mdisp'] in V[a] else 0
        r['tdown']=r['pTD'] in TDOWN
        r['nm']=tdname(r['pTD'])
        r['isU']=r['nm'].startswith('.?AU')
        r['isV']=r['nm'].startswith('.?AV')
        rows.append(r)
print('样本 %d ; L=1 %d ; L=0 %d\n'%(len(rows),sum(r['L'] for r in rows),sum(1 for r in rows if not r['L'])))
def ev(name,f):
    tp=sum(1 for r in rows if r['L'] and f(r)); fp=sum(1 for r in rows if not r['L'] and f(r))
    fn=sum(1 for r in rows if r['L'] and not f(r)); tn=sum(1 for r in rows if not r['L'] and not f(r))
    print('%-40s %s TP=%-4d FN=%-3d FP=%-3d TN=%-4d'%(name,'PERFECT' if fn==0==fp else '       ',tp,fn,fp,tn))
    return fn==0 and fp==0
cands=[('isU (pTD 名 .?AU 前缀)',lambda r:r['isU']),
       ('isV (pTD 名 .?AV 前缀)',lambda r:r['isV']),
       ('isU ∨ tdown',lambda r:r['isU'] or r['tdown']),
       ('isU ∧ pdisp==-1',lambda r:r['isU'] and r['pdisp']==-1),
       ('¬isV ∨ tdown',lambda r:(not r['isV']) or r['tdown']),
       ('isU ∨ (isV ∧ tdown)',lambda r:r['isU'] or (r['isV'] and r['tdown'])),
      ]
perf=[n for n,f in cands if ev(n,f)]
print('\nPERFECT 谓词：%s'%perf)
print('\n=== L 与 pTD 名前缀交叉 ===')
for lbl in (1,0):
    sub=[r for r in rows if r['L']==lbl]
    print(' L=%d n=%-4d  U前缀=%-4d V前缀=%-4d 其他=%-3d tdown=%d'%(lbl,len(sub),
        sum(r['isU'] for r in sub),sum(r['isV'] for r in sub),
        sum(1 for r in sub if not r['isU'] and not r['isV']),sum(r['tdown'] for r in sub)))
print('\n=== L=1 & mdisp==4 的 pTD 分布 ===')
sub=[r for r in rows if r['L']==1 and r['mdisp']==4]
for k,v in collections.Counter((hex(r['pTD']),r['nm']) for r in sub).most_common(10):
    print('   %s  %-40s n=%d'%(k[0],k[1],v))
print('\n=== L=0 的 pTD 分布 ===')
for k,v in collections.Counter((hex(r['pTD']),r['nm']) for r in rows if not r['L']).most_common(10):
    print('   %s  %-44s n=%d'%(k[0],k[1],v))
json.dump({'n':len(rows),'perfect':perf,
  'L1_u':sum(r['isU'] for r in rows if r['L']),'L1_v':sum(r['isV'] for r in rows if r['L']),
  'L0_u':sum(r['isU'] for r in rows if not r['L']),'L0_v':sum(r['isV'] for r in rows if not r['L'])},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c10.json','w'),indent=1)
