#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m17：30 个「pad0=4 且无 24B 项」的块定性（m14/m16 反例）。"""
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
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
sel=[a for a in CHD[1:] if pBCA[a]==CHD[IDX[a]-1]+40 and NB[a]]
print('候选 30 型块 %d 个'%len(sel))
print(' n 分布',collections.Counter(NB[a] for a in sel).most_common())
print(' 视图数分布',collections.Counter(len(G[a]) for a in sel).most_common())
print(' attributes',collections.Counter(P.dw(a+4) for a in sel).most_common())
print(' BCA[0]==自身 pTD 的 BCD:',sum(1 for a in sel if P.dw(BCA[a][0])==P.dw(a+28)),'/',len(sel))
print(' 前一记录 head%8:',collections.Counter(CHD[IDX[a]-1]%8 for a in sel).most_common())
print(' pad1 分布',collections.Counter(a-(pBCA[a]+4*NB[a]) for a in sel).most_common())
print(' 这些类的 BCA 中「已出现过」的 BCD 数：')
seen=set(BCA[CHD[0]]); firsts={}
for a in CHD[1:]:
    firsts[a]=len(set(BCA[a])-seen); seen|=set(BCA[a])
print('  first-new 数分布',collections.Counter(firsts[a] for a in sel).most_common())
print(' 全部 953 块的 first-new 数分布',collections.Counter(firsts.values()).most_common(8))
print(' 对照 205 型（pad0=0,无项）：n 分布',collections.Counter(NB[a] for a in CHD[1:] if pBCA[a]==CHD[IDX[a]-1]+36).most_common())
print(' 对照 205 型 first-new 分布',collections.Counter(firsts[a] for a in CHD[1:] if pBCA[a]==CHD[IDX[a]-1]+36).most_common())
print('\n 逐条 30 条明细：')
for a in sel[:12]:
    print('  head=0x%x n=%d views=%d BCA=%s lo=0x%x 值=%s'%(a,NB[a],len(G[a]),[hex(x) for x in BCA[a]],
      CHD[IDX[a]-1]+36,[hex(P.dw(CHD[IDX[a]-1]+36+4*k) or 0) for k in range(3)]))
