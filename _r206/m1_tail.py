#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m1：CHD 记录尾部归属（R205 未取得项①）+36/+40/+44 与跨度 L 的交叉表。
正控：已知 954/954 自指 +32；反控：错位 +32 偏移 7 档应 0 命中。"""
import sys,struct,collections
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
NEXT={a:(CHD[i+1] if i+1<len(CHD) else None) for i,a in enumerate(CHD)}
def cls(v):
    if v is None: return 'none'
    if v==0: return 'zero'
    w=P.where(v)
    if w in ('.text','.rdata','.data'): return w
    if v==0xffffffff: return '-1'
    return 'nonptr'
print('== A. 跨度 L 与 +36/+40/+44 交叉 ==')
xt=collections.Counter()
for a in CHD:
    L=NEXT[a]-a if NEXT[a] else -1
    xt[(L,cls(P.dw(a+36)),cls(P.dw(a+40)),cls(P.dw(a+44)))]+=1
for k,v in sorted(xt.items(),key=lambda x:-x[1])[:25]: print('  L=%s +36=%s +40=%s +44=%s : %d'%(k[0],k[1],k[2],k[3],v))
print('== B. 跨度分布 ==')
print(' ',collections.Counter((NEXT[a]-a) if NEXT[a] else -1 for a in CHD).most_common())
print('== C. +36 非零的 205 条：目标内容 ==')
t36=[a for a in CHD if P.dw(a+36)]
print(' count',len(t36),'L dist',collections.Counter(NEXT[a]-a for a in t36).most_common())
k=collections.Counter()
for a in t36:
    t=P.dw(a+36)
    k[(P.where(t),P.dw(t),P.dw(t+4),P.dw(t+8))]+=1
print(' target[0:3] dist',k.most_common(8))
print('  target in COL?',sum(1 for a in t36 if P.dw(a+36) in COL),'in CHD?',sum(1 for a in t36 if P.dw(a+36) in set(CHD)))
print('  sample',[(hex(a),hex(P.dw(a+36)),hex(P.dw(P.dw(a+36)) or 0)) for a in t36[:4]])
print('== D. +40 指向 .data 的 624 条：目标链 ==')
t40=[a for a in CHD if cls(P.dw(a+40))=='.data']
print(' count',len(t40),'L dist',collections.Counter(NEXT[a]-a for a in t40).most_common())
k=collections.Counter(); depth=[]
for a in t40:
    t=P.dw(a+40); v=P.dw(t); k[(P.where(v),)]+=1
    depth.append((hex(a),hex(t),hex(v or 0),P.where(v)))
print(' 1st-hop section',k.most_common())
print(' sample',depth[:5])
# +40 目标是否等于某类的 pTD / 某 CHD 的 +40 与 pTD 集合关系
ptds=set(P.dw(a+28) for a in CHD)
print(' +40 value in pTD set:',sum(1 for a in t40 if P.dw(a+40) in ptds))
print(' +40 first-hop target in pTD set:',sum(1 for a in t40 if P.dw(P.dw(a+40)) in ptds))
print('== E. +44 非零非零指针的 459 条 ==')
t44=[a for a in CHD if P.dw(a+44) not in (0,None) and cls(P.dw(a+44))=='nonptr']
print(' count',len(t44),'L dist',collections.Counter(NEXT[a]-a for a in t44).most_common())
print(' values top10',collections.Counter(P.dw(a+44) for a in t44).most_common(10))
print(' lowbyte dist',collections.Counter(P.dw(a+44)&0xff for a in t44).most_common(6))
print('== F. 正反控：自指 +32 ==')
ok=sum(1 for a in CHD if P.dw(a+32)==a); print(' +32==self %d/954'%ok)
for d in (-8,-4,4,8,12,16,20):
    print('  shift %+d : %d'%(d,sum(1 for a in CHD if P.dw(a+32+d)==a)))
print('== G. +36..+47 原始 dword 逐条前 12 例 ==')
for a in CHD[:12]:
    print(' 0x%x L=%s +16..+44=%s'%(a,NEXT[a]-a,[hex(P.dw(a+o) or 0) for o in range(16,48,4)]))
