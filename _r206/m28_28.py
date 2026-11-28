#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m28：把 m27 三条 FAIL 钉死成实测值（不预设 280/264 等数字）。"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4])
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); IDX={a:i for i,a in enumerate(CHD)}
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
TDOK=lambda td: P.where(td)=='.data' and (P.cstr(td+8,200) or b'').startswith(b'.?A')
def parse(n):
    lo=CHD[IDX[n]-1]+36; p=pBCA[n]; k=NB[n]
    for pad0 in (0,4):
        q=lo+pad0
        if q>p or (p-q)%24: continue
        items=[]
        for j in range((p-q)//24):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==n: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: items=None; break
        if items is None: continue
        if [P.dw(p+4*j) for j in range(k)]!=BCA[n]: continue
        if n-(p+4*k) not in (4,8): continue
        return (pad0,q,items,p+4*k)
    return None
B={a:parse(a) for a in CHD[1:]}; B={a:b for a,b in B.items() if b}
owner={}
for a,b in B.items():
    for t,tp in b[2]:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
print('== 多引用样本实测 ==')
multi=[b for b in owner if len(refs[b])>1]
gt=[b for b in multi if [y for y in refs[b] if y>b]]
print(' 多引用 %d 条；其中存在引用者>BCD 地址 %d 条；不存在 %d 条'%(len(multi),len(gt),len(multi)-len(gt)))
print(' 不存在引用者>BCD 的那 %d 条：持有块==min全部引用者？'%(len(multi)-len(gt)),
      sum(1 for b in multi if b not in gt and owner[b]==min(refs[b])))
print(' 判别样本 %d 条上：min %d / max %d / 最近 %d'%(len(gt),
      sum(1 for b in gt if owner[b]==min(refs[b])),
      sum(1 for b in gt if owner[b]==max(refs[b])),
      sum(1 for b in gt if owner[b]==min(refs[b],key=lambda y:abs(y-b)))))
print(' 全 1002 条上：min %d / max %d / 最近 %d'%(
      sum(1 for b in owner if owner[b]==min(refs[b])),
      sum(1 for b in owner if owner[b]==max(refs[b])),
      sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b)))))
ckmin=sum(1 for b in owner if owner[b]==min(refs[b]))
fromlaw=sum(1 for b in owner if owner[b]==min([y for y in refs[b] if y>b]))
print(' 律3 原文（min{HEAD>BCD}）= %d/1002；简化为 min{全部引用者} = %d/1002'%(fromlaw,ckmin))
print('== 30 条 pad0=4 无项的 +44 ==')
s30=[a for a in CHD[:-1] if B.get(CHD[IDX[a]+1]) and not B[CHD[IDX[a]+1]][2] and B[CHD[IDX[a]+1]][0]==4]
print(' 30 条 +44 值分布:',collections.Counter(P.dw(a+44) for a in s30).most_common(8))
ex=[]
for a in s30[:5]:
    nx=CHD[IDX[a]+1]; p=pBCA[nx]
    print('  head=0x%x next=0x%x pBCA=0x%x n=%d BCA=%s +36=%s +40=%s +44=%s'%(
      a,nx,p,NB[nx],[hex(P.dw(p+4*j)) for j in range(NB[nx])],
      hex(P.dw(a+36) or 0),hex(P.dw(a+40) or 0),hex(P.dw(a+44) or 0)))
    ex.append(a)
# 检查 +44 与哪个量相等
def cand(a):
    nx=CHD[IDX[a]+1]; p=pBCA[nx]; out={}
    out['BCA0.pTD']=P.dw(P.dw(p))
    out['BCA1.mdisp']=s32(P.dw(P.dw(p+4)+8))
    out['BCA0.mdisp']=s32(P.dw(P.dw(p)+8))
    out['BCA1.numContained']=P.dw(P.dw(p+4)+4)
    out['pBCA%%8']=p%8
    out['next+4']=P.dw(nx+4)
    return out
for a in ex:
    print('  0x%x +44=%s cands=%s'%(a,P.dw(a+44),cand(a)))
print(' 全 30 条各候选命中数:',{k:sum(1 for a in s30 if P.dw(a+44)==v) for k,v in [('BCA0.pTD',None)]} if False else '')
hits=collections.Counter()
for a in s30:
    for k,v in cand(a).items():
        if P.dw(a+44)==v: hits[k]+=1
print(' ',hits.most_common())
