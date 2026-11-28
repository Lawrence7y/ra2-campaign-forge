#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十三刀：定位 m12 Z2 的 80 张「真 != posrev 但无分枝点」的 CHD。
m12 自错一条：S22 Z2a 假设「真 != posrev」与「有分枝点」等价；实测 19/99，尚有 80 张无分枝点却偏离 posrev。
本刀给出这 80 张的形态：它们在无分枝（即每个结点 <=1 子结点）的前提下偏离位置逆序，
唯一可能是 ncb 的**递减步长不是每步 1**（跳号），即某些层被折叠。
G1 对 n=2 的 CHD 单独看：ncb 只能是 [1,0]，与 posrev 相同 ⇒ n<=2 恒相等。
G2 给出 80 张的 (n, ncb 序列, md 序列) 全部明细并归类。
"""
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
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
    d['ncb']=[P.dw(b+4) for b in d['bcds']]
    d['md']=[s32(P.dw(b+8)) for b in d['bcds']]
def kids_of(ncb,n):
    out={};i=0
    while i<n:
        end=i+ncb[i]
        if end>=n: return None
        k=i+1;ks=[]
        while k<=end:
            ks.append(k);k=k+ncb[k]+1
            if k==0: return None
        if k!=end+1: return None
        out[i]=ks;i=end+1
    return out if i==n else None
gap=[]
for v,d in CHD.items():
    ncb=d['ncb'];n=d['n']
    pr=[n-1-j for j in range(n)]
    if ncb==pr: continue
    ks=kids_of(ncb,n)
    if ks is None: gap.append((v,n,ncb,d['md'],'PARSE_FAIL')); continue
    br=sum(1 for i in ks if len(ks[i])>=2)
    if br==0: gap.append((v,n,ncb,d['md'],'NO_BRANCH'))
print('=== 80 张「无分枝却偏离 posrev」明细 ===')
for v,n,ncb,md,tag in gap:
    print(' CHD %08X n=%2d ncb=%s md=%s %s'%(v,n,ncb,md,tag))
print('  总数 =',len(gap))
# 归类：ncb 与 posrev 的差是否恒定
cls=collections.Counter()
for v,n,ncb,md,tag in gap:
    pr=[n-1-j for j in range(n)]
    diffs=[ncb[i]-pr[i] for i in range(n)]
    cls[tuple(sorted(set(diffs)))]+=1
print('  差集形态（ncb - posrev 的不同值集合 -> 张数）:',dict(cls))
# 检验新模型：ncb = 该结点之后（更深）的叶子数 + 该结点子树内非叶子层数？先给子树大小
sizes=collections.Counter()
for v,n,ncb,md,tag in gap:
    for c in ncb: sizes[c+1]+=1
print('  这 80 张的子树大小分布:',dict(sorted(sizes.items())))
json.dump(dict(gap=[dict(chd=hex(v),n=n,ncb=ncb,md=md,tag=tag) for v,n,ncb,md,tag in gap],
  cls={'|'.join(map(str,k)):v for k,v in cls.items()}),open('_r196/m13_gap80.json','w'),ensure_ascii=False,indent=1)
