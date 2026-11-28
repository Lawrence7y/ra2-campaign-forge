#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m1：CHD+16 处的记录是不是该类自己的 COL（R204 未取得项④：CHD +16 之后是否还有字段）。
判据全部可复算；反控三条。
"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
ck('V0 基数 COL1214/VTI1214/CHD954',(len(COL),len(VTI),len(G))==(1214,1214,954),(len(COL),len(VTI),len(G)))

# 每个 CHD 的自有 pTD（从 mdisp==0 的 BCD 取，R204 QG5 已证 <=> 自有）
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
def self_td(a):
    for b in BCA[a]:
        if s32(P.dw(b+8))==0: return P.dw(b)
    return None
STD={a:self_td(a) for a in CHD}
ck('V1 每 CHD 恰 1 条 mdisp==0 的 BCD（R204 QG5 复现）',
   all(sum(1 for b in BCA[a] if s32(P.dw(b+8))==0)==1 for a in CHD),
   collections.Counter(sum(1 for b in BCA[a] if s32(P.dw(b+8))==0) for a in CHD))

# ---- H1: CHD+16 处是 COL 记录（sig,mdisp,pdisp,pTD,pCHD）----
h=dict(sig=0,mdisp=0,cd=0,ptd=0,pchd_self=0,full=0)
bad=[]
for a in CHD:
    sig=P.dw(a+16); md=s32(P.dw(a+20)); cd=P.dw(a+24); ptd=P.dw(a+28); pc=P.dw(a+32)
    if sig in (0,1,2): h['sig']+=1
    if md==0: h['mdisp']+=1
    if cd==0: h['cd']+=1
    if ptd==STD[a]: h['ptd']+=1
    if pc==a: h['pchd_self']+=1
    if sig in (0,1) and md==0 and cd==0 and ptd==STD[a] and pc==a: h['full']+=1
    else: bad.append((a,COL[G[a][0]]['name'][:30],sig,md,cd,hex(ptd or 0),hex(pc or 0),hex(STD[a] or 0)))
print('   H1 各字段命中:',h,' 反例数',len(bad))
for t in bad[:8]: print('    bad',t)
ck('H1a CHD+16 的 sig 属 {0,1,2} 954/954',h['sig']==954,h['sig'])
ck('H1b CHD+20 mdisp == 0 954/954',h['mdisp']==954,h['mdisp'])
ck('H1c CHD+24 cdOffset == 0 954/954',h['cd']==954,h['cd'])
ck('H1d CHD+28 pTD == 该类自有 pTD 954/954',h['ptd']==954,h['ptd'])
ck('H1e CHD+32 pCHD == 该 CHD 自身 954/954',h['pchd_self']==954,h['pchd_self'])
ck('H1f 五条同时成立（=> CHD+16 是一个完整 COL 记录）954/954',h['full']==954,h['full'])

# ---- H2: 这 954 个类级 COL 与 1214 个视图 COL 的关系 ----
CLSCOL={a+16 for a in CHD}
ck('H2a 954 个类级 COL 互异',len(CLSCOL)==954,len(CLSCOL))
ck('H2b 与 1214 个视图 COL 不相交',len(CLSCOL & set(COL))==0,len(CLSCOL & set(COL)))
print('   H2 类级 COL 中 sig 分布 %s'%collections.Counter(P.dw(x) for x in CLSCOL).most_common())
# 视图 COL -> 类级 COL 的映射（按类名）
view_names={c:v['name'] for c,v in COL.items()}
cls_by_name=collections.defaultdict(list)
for a in CHD: cls_by_name[COL[G[a][0]]['name']].append(a+16)
ck('H2c 每个类名恰 1 个类级 COL',all(len(v)==1 for v in cls_by_name.values()),len(cls_by_name))

# ---- H3: 1214 视图 COL 的 pCHD 是否都指向 954 CHD；类级 COL 的 pCHD 也指同 CHD ----
ck('H3a 视图 COL 的 pCHD ∈ 954 CHD 集合',all(v['pchd'] in G for v in COL.values()),len(set(v['pchd'] for v in COL.values())))
# 每个 CHD 被多少视图 COL 引用 与 pCHD 分组大小一致
c2=collections.Counter(v['pchd'] for v in COL.values())
ck('H3b 视图 COL 按 pCHD 计数 == R203 视图数分布',
   dict(collections.Counter(c2.values()))=={1:860,2:10,3:6,4:76,5:1,7:1},dict(collections.Counter(c2.values())))

# ---- H4: BCD 数组起点 == CHD+40 的类占比；以及 gap 构成 ----
at40=0; arr=[]
for a in CHD:
    b0=BCA[a][-1]
    if b0==a+40: at40+=1
print('   H4 BCA 末元素 == CHD+40 的类数:',at40,'/',len(CHD))
# BCD 是否落在同一连续 24 步长数组
runs=0
for a in CHD:
    v=sorted(BCA[a])
    if all(v[i+1]-v[i]==24 for i in range(len(v)-1)): runs+=1
print('   H4 BCA 升序后差分恒 24 的类数:',runs,'/',len(CHD))

# ---- H5 反控 ----
import random
random.seed(205)
# 反控1：把 CHD+16 换成 CHD+20（错位 4 字节）
ok=0
for a in CHD:
    sig=P.dw(a+20); md=s32(P.dw(a+24)); cd=P.dw(a+28); ptd=P.dw(a+32); pc=P.dw(a+36)
    if sig in (0,1) and md==0 and cd==0 and ptd==STD[a] and pc==a: ok+=1
ck('C1 反控：整体错位 4 字节后 0/954',ok==0,ok)
# 反控2：随机 .rdata 地址做同样的五元判据
cnt=0
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
for _ in range(2000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    sig=P.dw(x); md=s32(P.dw(x+4)); cd=P.dw(x+8); ptd=P.dw(x+12); pc=P.dw(x+16)
    if sig in (0,1) and md==0 and cd==0 and pc==x and ptd in set(v for v in STD.values()): cnt+=1
ck('C2 反控：2000 个随机 .rdata 地址命中该五元判据 0 次',cnt==0,cnt)
# 反控3：pCHD==自身 这条单独在随机地址上的命中率（说明它不是恒真）
cnt3=0
for _ in range(2000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x+16)==x: cnt3+=1
ck('C3 反控：随机地址 x+16 处等于自身 0 次',cnt3==0,cnt3)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
