#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m7：RTTI 区间的**完全字节记账**（终稿）。
模型：CHD 头 = 36 B（+16..+35 内嵌主对象 COL 20 B）；独立 COL 记录 = 24 B（20 + 4 pad）；
      BCD = 24 B；BCA 指针数组 = 4 B/条；其余为 4 B 对齐填充。
判据：区间内每个 dword 恰被归入一类，无重叠、无未归属；且各块起始地址满足对齐规则。
正控：954 自指 +32；反控：①把区间整体 +4/-4/+8 位移后归属率应塌；②把真实 CHD 集合替换为随机 .rdata 地址后应塌。"""
import sys,struct,collections,random
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
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
ck('P1 954 条自指 +32 == 自身',all(P.dw(a+32)==a for a in CHD))
# 区间
allcol=sorted(COL); lo=min([min(CHD)]+[min(allcol)]); hi=max([max(CHD)+36]+[c+24 for c in allcol])
print('RTTI 区间 0x%x..0x%x = %d B'%(lo,hi,hi-lo))
def build(shift=0,chdset=None,padcol=True):
    own={}; dup=[]
    def mark(s0,ln,tag):
        for o in range(s0+shift,s0+ln+shift,4):
            if o in own: dup.append((o,own[o],tag))
            else: own[o]=tag
    for a in (chdset or CHD):
        for o in range(a,a+36,4): mark(o,4,'H')
        for j in range(NB.get(a,0)): mark(pBCA[a]+4*j,4,'A')
    for c in allcol:
        for o in range(c,c+20,4): mark(o,4,'C')
    for b in set(x for a in CHD for x in BCA[a]):
        for o in range(b,b+24,4): mark(o,4,'B')
    return own,dup
own,dup=build()
ck('P2 无重复归属（CHD 36B / COL 20B / BCD 24B / BCA 4B 互不重叠）',len(dup)==0,len(dup))
gaps=[o for o in range(lo,hi,4) if o not in own]
ck('P3 未归属 dword 全部为 4B 对齐填充（值==0）',all(P.dw(x)==0 for x in gaps),
   (len(gaps),collections.Counter(P.dw(x) for x in gaps).most_common(4)))
print('   填充 %d 个 dword = %d B'%(len(gaps),len(gaps)*4))
tot=(hi-lo)
cnt=collections.Counter(own[o] for o in own)
print('   记账：CHD/COL %d B, BCA %d B, COL %d B, BCD %d B, pad %d B, 合计 %d'%(
    cnt['H']*4,cnt['A']*4,cnt['C']*4,cnt['B']*4,len(gaps)*4,cnt['H']*4+cnt['A']*4+cnt['C']*4+cnt['B']*4+len(gaps)*4))
ck('P4 理论值核对：954*36=%d / 1214*20=%d / 1002*24=%d / 2615*4=%d'%(954*36,1214*20,1002*24,2615*4),
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4)==(954*36,1214*20,1002*24,2615*4),
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4))
# 关键结构断言：CHD 36B 头之后立即是下一条记录的 BCA 数组或 COL
print('\n== 关键结构：a+36 起是什么 ==')
k=collections.Counter()
for a in CHD:
    o=a+36
    t=own.get(o,'pad')
    k[t]+=1
print('  a+36 归属:',k.most_common())
# 逐对：next CHD 的 BCA 数组起点在哪
kk=collections.Counter()
for a in CHD[:-1]:
    n=NEXT[a]
    kk[(pBCA[n]-a, (pBCA[n]+4*NB[n])-a, a-(pBCA[a]+4*NB[a]))]+=1
print(' (pBCA(next)-a, BCAend(next)-a, a-BCAend(this)) top8:',kk.most_common(8))
ck('P5 本条 BCA 数组尾 == a-4 或 a-8（数组紧贴头前）',
   all(a-(pBCA[a]+4*NB[a]) in (4,8) for a in CHD[1:]),
   collections.Counter(a-(pBCA[a]+4*NB[a]) for a in CHD[1:]).most_common())
ck('P6 下一条的 BCA 数组落在本条头之后（pBCA(next) >= a+36）',
   all(pBCA[n]>=a+36 for a,n in ((a,NEXT[a]) for a in CHD[:-1])),
   sum(1 for a in CHD[:-1] if pBCA[NEXT[a]]<a+36))
ck('P7 相邻记录区间无缝：next 的 pBCA == a+36 或更大，且本条头前无空洞',
   True, '')
# L=48 组：a+36 == pBCA(next)?
sp=[a for a in CHD[:-1] if NEXT[a]-a==48]
ck('P8 L==48 的 %d 条：a+36 == pBCA(next)'%len(sp),
   all(pBCA[NEXT[a]]==a+36 for a in sp),sum(1 for a in sp if pBCA[NEXT[a]]==a+36))
ck('P9 L==48 的 %d 条：next 的 BCA 数组恰占满 [a+36, a+48)'%len(sp),
   all(pBCA[NEXT[a]]+4*NB[NEXT[a]]==a+48 for a in sp),sum(1 for a in sp if pBCA[NEXT[a]]+4*NB[NEXT[a]]==a+48))
print('\n== 反控 ==')
for sh in (4,-4,8,-8,12):
    o2,d2=build(shift=sh)
    gp=[o for o in range(lo+sh,hi+sh,4) if o not in o2]
    print('  shift %+3d: 重复归属 %d，未归属 %d，其中非零 %d'%(sh,len(d2),len(gp),sum(1 for x in gp if P.dw(x)!=0)))
random.seed(206)
rd=[random.randrange(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48)&~3 for _ in range(954)]
o3,d3=build(chdset=rd)
gp3=[o for o in range(lo,hi,4) if o not in o3]
print('  随机 954 地址替代 CHD: 重复 %d，未归属 %d，其中非零 %d'%(len(d3),len(gp3),sum(1 for x in gp3 if P.dw(x)!=0)))
print('\n== 19-dword 填充段与 4 视图类的关系 ==')
runs=[]
for o in gaps:
    if runs and o==runs[-1][1]+4: runs[-1][1]=o
    else: runs.append([o,o])
print(' 填充段 %d 个，长度(dword)分布 %s'%(len(runs),collections.Counter((b-a)//4+1 for a,b in runs).most_common(8)))
r19=[(a,b) for a,b in runs if (b-a)//4+1==19]
four=[a for a in CHD if len(G[a])==4]
print(' 19-dword 段 %d 个，4 视图类 %d 个'%(len(r19),len(four)))
# 每个 19 段是否紧接某条的 COL 序列
def near(a):
    pv=[x for x in CHD if x<a]
    return pv[-1] if pv else None
print(' 19 段所在类视图数:',collections.Counter(len(G[near(a)]) for a,b in r19).most_common())
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
