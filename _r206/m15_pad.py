#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m15：pad0==4 且无 24B 项的 30 个块的形态（m14 B3 反例定位）。"""
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); IDX={a:i for i,a in enumerate(CHD)}
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
TDOK=lambda td: P.where(td)=='.data' and (P.cstr(td+8,200) or b'').startswith(b'.?A')
rows=[]
for a in CHD[1:]:
    lo=CHD[IDX[a]-1]+36; n=NB[a]; p=pBCA[a]
    # 本块是否含 24B 项
    hasitem = (p-lo)==0 or (p-(lo+4 if (p-lo)%24==4 else lo))%24!=0 and False
    pad0 = 0 if (p-lo)%24==0 and p==lo else (4 if (p-lo-4)%24==0 and p>lo else None)
    rows.append((a,lo,p,n,a-(p+4*n),p-lo,pad0))
k=collections.Counter((r[5],r[3],r[4]) for r in rows)
print(' (pBCA-lo, n, pad1) 分布:',k.most_common(10))
sel=[r for r in rows if r[5]==4]
print(' pBCA-lo==4 的块数 %d，其 (n,pad1):'%len(sel),collections.Counter((r[3],r[4]) for r in sel).most_common())
print(' 样例 6 条:')
for r in sel[:6]:
    a,lo,p,n,pad1,dl,pad0=r
    print('  head=0x%x lo=0x%x pBCA=0x%x n=%d pad1=%d  头前 8 dword=%s'%(
        a,lo,p,n,pad1,[hex(P.dw(lo+4*k2) or 0) for k2 in range(0,6)]))
print(' 这些块的 pBCA%8:',collections.Counter(r[2]%8 for r in sel).most_common())
print(' 这些块的 lo%8:',collections.Counter(r[1]%8 for r in sel).most_common())
print(' 这些块 BCA 条目数:',collections.Counter(r[3] for r in sel).most_common())
print(' BCA 为 2 条的块总数:',sum(1 for r in rows if r[3]==2))
