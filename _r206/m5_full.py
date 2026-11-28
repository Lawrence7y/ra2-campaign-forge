#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m5：RTTI 区块的**完全字节记账**（full byte accounting）。
模型：每个类块 = [BCD 数组(24*k 字节, 8 对齐)][BCA 数组(4*n)][CHD 16B][内嵌 COL 20B]，
      数组落在 (prev_CHD+36, 本 CHD) 区间内；BCD 是 COMDAT 折叠后的共享池。
判据：区间内每一个 dword 都能被归入且仅归入一类（CHD/COL 字段 / BCA 条目 / BCD 字段 / 对齐零）。
正控：954 自指 +32。反控：把区间整体位移 ±4/±8 后记账率应塌。"""
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
PREV={a:(CHD[i-1] if i>0 else None) for i,a in enumerate(CHD)}
NEXT={a:(CHD[i+1] if i+1<len(CHD) else None) for i,a in enumerate(CHD)}
N={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(N[a])] for a in CHD}
NV=sum(N.values())
print('CHD %d, BCA 条目总 %d'%(len(CHD),NV))
# 记账表
own={}; dup=[]
def mark(lo,ln,tag):
    for o in range(lo,lo+ln,4):
        if o in own: dup.append((o,own[o],tag))
        else: own[o]=tag
for a in CHD:
    for o in range(a,a+36,4): mark(o,4,'CHD/COL')
    for j in range(N[a]): mark(pBCA[a]+4*j,4,'BCA')
bset=set(b for a in CHD for b in BCA[a])
for b in bset:
    for o in range(b,b+24,4): mark(o,4,'BCD')
lo=min(own); hi=max(own)+4
print('记账区间 0x%x..0x%x  跨度 %d B'%(lo,hi,hi-lo))
print('重复归属 %d 处，样例 %s'%(len(dup),dup[:5]))
gap=[o for o in range(lo,hi,4) if o not in own]
print('未归入 dword %d 个（%d B）'%(len(gap),len(gap)*4))
print(' 前缀 gap:',[hex(x) for x in gap[:12]])
print(' 值分布:',collections.Counter(P.dw(x) for x in gap).most_common(6))
# 尾部分组：连续 gap 段
runs=[]; 
for o in gap:
    if runs and o==runs[-1][1]+4: runs[-1][1]=o
    else: runs.append([o,o])
print(' gap 段数 %d，长度分布 %s'%(len(runs),collections.Counter((b-a)//4+1 for a,b in runs).most_common(10)))
print(' 段起点样例:',[hex(a) for a,b in runs[:12]])
# 相对位置：gap 段相对前一条 CHD
rel=collections.Counter()
for a,b in runs:
    pv=[x for x in CHD if x<a]
    if pv: rel[(a-pv[-1])]+=1
    else: rel['head']+=1
print(' gap 段起点相对前一 CHD 偏移:',rel.most_common(12))
# 每个区间的字节构成
print('\n== 区间 [prev+36, a) 的构成（前 12 例）==')
for a in CHD[1:13]:
    pv=PREV[a]; seg=range(pv+36,a,4)
    cat=collections.Counter(own.get(o,'GAP') for o in seg)
    print('  0x%x (prev 0x%x, %d B) %s'%(a,pv,a-pv-36,dict(cat)))
# 结构化：BCD 数组是否紧贴本 CHD 之前
print('\n== BCD 数组与本 CHD 的相对位置 ==')
k=collections.Counter()
for a in CHD:
    ents=BCA[a]
    k[(pBCA[a]+4*N[a]==a, a-(pBCA[a]+4*N[a]), min(ents)<pBCA[a], max(ents)<pBCA[a])]+=1
print(' (BCA尾==CHD, CHD-BCA尾, min<BCA, max<BCA):',k.most_common(6))
print('\n== BCA 条目是否降序（BCA[0]=自身 BCD）==')
dec=sum(1 for a in CHD if all(BCA[a][i]>BCA[a][i+1] for i in range(len(BCA[a])-1)))
print(' 严格降序 %d/954；BCA[0]==自身 pTD 的 BCD %d/954'%(dec,
   sum(1 for a in CHD if P.dw(BCA[a][0])==P.dw(a+28))))
print('\n== BCD 池 ==')
print(' 唯一 BCD 数 %d，被引 2615 条'%len(bset))
print(' BCD 地址 mod 8:',collections.Counter(b%8 for b in bset).most_common())
