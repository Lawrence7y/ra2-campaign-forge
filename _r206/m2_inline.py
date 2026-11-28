#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m2：CHD 跨度 L 的构成 —— pBCA(数组本身)/BCD 是否 inline 落在 [a, next) 内。
正控：954 条 pBCA 全 .rdata；反控：把窗口整体位移 ±4/±8 后 inline 命中应塌。"""
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
NEXT={a:(CHD[i+1] if i+1<len(CHD) else CHD[-1]+0x100) for i,a in enumerate(CHD)}
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
print('== A. pBCA 数组地址是否落在本记录窗口 [a,next) ==')
ins=0; dist=collections.Counter()
for a in CHD:
    p=P.dw(a+12)
    if a<=p<NEXT[a]: ins+=1; dist[p-a]+=1
    else: dist[('out',P.where(p))]+=1
print(' inline pBCA %d/954'%ins,' offset(a->pBCA) top', collections.Counter({k:v for k,v in dist.items() if isinstance(k,int)}).most_common(10))
print(' pBCA-a 与 numBase 关系:', collections.Counter((dist.get(k,0),k) for k in [] ).most_common())
n0=[a for a in CHD if P.dw(a+12)>=a]
print(' 样例 (a, numBase, pBCA-a, L):',[(hex(a),P.dw(a+8),hex(P.dw(a+12)-a),NEXT[a]-a) for a in CHD[:6]])
print('== B. BCD(BCA 条目) 是否落在窗口内 ==')
inn=0; outn=0; per=collections.Counter()
for a in CHD:
    k=sum(1 for b in BCA[a] if a<=b<NEXT[a])
    per[(k,len(BCA[a]))]+=1
    inn+=k; outn+=len(BCA[a])-k
print(' BCA 条目总 %d，窗口内 %d，窗口外 %d'%(inn+outn,inn,outn))
print(' (窗口内数, |BCA|) top',per.most_common(8))
print('== C. L 与 numBaseClasses 的算术关系（试 L = 40 + 4n / 48+4n / 40+24n ...）==')
forms={'40+4n':lambda n:40+4*n,'48+4n':lambda n:48+4*n,'40+8n':lambda n:40+8*n,'48+8n':lambda n:48+8*n,
       '40+24n':lambda n:40+24*n,'48+24n':lambda n:48+24*n,'16+24n':lambda n:16+24*n,'24n+16+4n':lambda n:28*n+16}
for nm,f in forms.items():
    print('  %-8s hit %d/953'%(nm,sum(1 for a in CHD[:-1] if NEXT[a]-a==f(P.dw(a+8)))))
print('== D. 逐条明细前 20（a, L, n, pBCA-a, BCA在窗口内数）==')
for a in CHD[:20]:
    print('  0x%x L=%3d n=%2d pBCA-a=%s in=%d +36=%s +40=%s +44=%s'%(
        a,NEXT[a]-a,P.dw(a+8),hex(P.dw(a+12)-a) if P.dw(a+12)>=a else 'OUT',
        sum(1 for b in BCA[a] if a<=b<NEXT[a]),hex(P.dw(a+36) or 0),hex(P.dw(a+40) or 0),hex(P.dw(a+44) or 0)))
