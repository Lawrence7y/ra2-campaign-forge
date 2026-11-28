#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m18：BCA 数组对齐规则的统计裁定（m14/m17 遗留）。"""
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); IDX={a:i for i,a in enumerate(CHD)}
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
print('pBCA%8 vs n:')
print(' ',collections.Counter((NB[a],pBCA[a]%8) for a in CHD).most_common(12))
print('pBCA%8 == 0 的 n 分布:',collections.Counter(NB[a] for a in CHD if pBCA[a]%8==0).most_common())
print('pBCA%8 == 4 的 n 分布:',collections.Counter(NB[a] for a in CHD if pBCA[a]%8==4).most_common())
print('\n首个 head 的 pBCA%8 =',pBCA[CHD[0]]%8,'n=',NB[CHD[0]])
# BCA 数组是否 8 对齐与 n>=2 完全对应
c=collections.Counter()
for a in CHD:
    c[(NB[a]>=2, pBCA[a]%8==0)]+=1
print('\n(n>=2, pBCA 8对齐):',c.most_common())
# 那些 n>=2 但 pBCA%8==4 的
bad=[a for a in CHD if NB[a]>=2 and pBCA[a]%8==4]
print('n>=2 且 pBCA%8==4 的个数',len(bad),[hex(x) for x in bad[:6]])
# 块内是否有 24B 项
def hasitems(a):
    if a==CHD[0]: return None
    lo=CHD[IDX[a]-1]+36; p=pBCA[a]
    return (p-lo)%24!=0 or p!=lo
print('这些块的 (pBCA-lo) 值:',collections.Counter(pBCA[a]-(CHD[IDX[a]-1]+36) for a in bad).most_common())
print('\n全部块 (pBCA-lo) 模 24 分布:',collections.Counter((pBCA[a]-(CHD[IDX[a]-1]+36))%24 for a in CHD[1:]).most_common())
