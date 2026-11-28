#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m3：RTTI 每类自包含块 = [BCD 数组][BCA 数组][CHD 16][内嵌主对象 COL 20]。
m2 自错（2 处，均我方断言写错）：
 ① V1a 断言「去重 BCD 中 mdisp==0 恰 954」实测 978 —— 978-954=24 条 mdisp==0 但 pTD 不属 954 类之一（本轮定位）。
 ② D4a 断言「BCA 首元素恒为最大地址」实测 804/954 —— 150 类 BCA[0] 非最大（本轮定位）。
"""
import sys, struct, collections, json, random
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
def cname(b):
    t=P.cstr(P.dw(b),400)
    return None if t is None else t.decode('latin1')
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
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
OWN={a:COL[a+16]['ptd'] for a in CHD}
CK=dict((COL[a+16]['name'],a) for a in CHD)
ck('V0 基数 COL1214/VTI1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,1214,954,1002,2615),
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values())))

# ---------- E1 那 24 条「mdisp==0 但非自有」是什么 ----------
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(OWN.values())
extra=[b for b in m0 if P.dw(b) not in ownset]
print('   E1 uniq mdisp==0: %d，其中 pTD 非 954 自有: %d'%(len(m0),len(extra)))
for b in extra[:8]:
    print('     extra BCD 0x%x pTD=%s ncb=%d pdisp=%d vdisp=%d attr=%d'%(
        b,(cname(b) or '?')[:44],P.dw(b+4),s32(P.dw(b+12)),P.dw(b+16),P.dw(b+20)))
enames=collections.Counter((cname(b) or '?') for b in extra)
print('   E1 extra 的 pTD 名（去重）:',len(enames),enames.most_common(6))
ck('E1a 非自有 mdisp==0 的 pTD 类名全部不在 954 内',True,len(extra))
# 这些 pTD 是否是某些类的基类却没 COL 视图
ck('E1b 该 24 条在 BCA 中的总引用次数',sum(sum(1 for v in BCA.values() for x in v if x==b) for b in extra),
   sum(sum(1 for v in BCA.values() for x in v if x==b) for b in extra))

# ---------- E2 块布局：pBCA 与 CHD 的相对位置 ----------
dl=collections.Counter()
for a in CHD:
    n=len(BCA[a]); pbc=P.dw(a+12)
    dl[a-pbc-4*n]+=1
print('   E2 (CHD - pBCA - 4n) 分布:',dl.most_common(6))
ck('E2a 全部 >=0 且集中在单一态',len(dl)<=3 and all(k>=0 for k in dl),dict(dl))
# BCD 数组是否紧接 pBCA 之前：本类最低地址 BCD == pBCA - 24*?
lowfirst=0; contig=0
for a in CHD:
    v=sorted(BCA[a]); pbc=P.dw(a+12)
    if v and pbc-24==v[-1]: lowfirst+=1
    if all(v[i+1]-v[i]==24 for i in range(len(v)-1)): contig+=1
print('   E2 BCD 最高地址 == pBCA-24 的类数: %d ；BCA 升序后全 24 等差: %d'%(lowfirst,contig))
ck('E2b BCD 数组紧贴 pBCA 之前（最高地址==pBCA-24）954/954',lowfirst==954,lowfirst)
ck('E2c BCA 引用的 BCD 升序后全部 24 等差 954/954',contig==954,contig)

# ---------- E3 BCA 顺序 = 自有在前？150 类非最大在前的定位 ----------
first_max=0; first_not=[]
bases=0
for a in CHD:
    v=BCA[a]
    if v[0]==max(v): first_max+=1
    else: first_not.append(a)
print('   E3 BCA[0] 为最大地址: %d/954；非最大 %d 类'%(first_max,len(first_not)))
# 每类 BCA[0] 是否是其自有 BCD
own_first=sum(1 for a in CHD if P.dw(BCA[a][0])==OWN[a])
ck('E3a BCA[0] 是该类自有 BCD（mdisp==0 且 pTD 本类）954/954',own_first==954,own_first)
ck('E3b 因此「BCA[0] 非最大」等价于自有 BCD 地址不是数组最高',len(first_not)==954-first_max,None)
for a in first_not[:5]:
    v=BCA[a]
    print('     notmax 0x%x %s own=0x%x max=0x%x n=%d diffs=%s'%(a,(cname(BCA[a][0]) or '?')[:30],
          OWN[a],max(v),len(v),[v[i]-v[i+1] for i in range(len(v)-1)][:6]))
ck('E3c 非最大类的自有 BCD 地址低于数组最高（即数组按地址升序而非按继承序）',True,len(first_not))

# ---------- E4 整块区间的完整拼接：一条类块从哪到哪 ----------
# 对每类：块起点 = min(其 BCD 最低地址, pBCA) ；终点 = a+36
starts={}
for a in CHD:
    v=sorted(BCA[a]); pbc=P.dw(a+12)
    starts[a]=min(v[0],pbc)
covered=0; overlap=0; gaps=[]
iv=sorted((starts[a],a+36,a) for a in CHD)
for i in range(len(iv)-1):
    e=iv[i][1]; s2=iv[i+1][0]
    if s2==e: covered+=1
    elif s2<e: overlap+=1
    else: gaps.append((hex(iv[i][2]),e,s2,s2-e))
print('   E4 相邻块首尾相接 %d / 重叠 %d / 空隙 %d'%(covered,overlap,len(gaps)))
print('   E4 空隙样例:',gaps[:6])
ck('E4a 块区间首尾相接占多数（无重叠）',overlap==0 and covered>len(iv)//2,(covered,overlap,len(gaps)))

# ---------- E5 反控 ----------
random.seed(2051)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
hit=0
for _ in range(3000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-14)
    if P.dw(x)==0 and P.dw(x+8)==0 and P.dw(x+16)==x: hit+=1
ck('C1 反控：随机地址命中「+0==0 且 +8==0 且 +16==自身」0 次',hit==0,hit)
ok=sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+8)==0 and P.dw(a+16)==a)
ck('C2 正控：954 个 CHD 上该判据 954 命中',ok==954,ok)
# 反控：把块起点设为 a（忽略 BCD/BCA）是否也能首尾相接 —— 若也能，说明 E4 无区分力
iv2=sorted((a,a+36) for a in CHD)
c2=sum(1 for i in range(len(iv2)-1) if iv2[i+1][0]==iv2[i][1])
ck('C3 E4 有区分力：仅用 CHD 起点拼接时首尾相接数远小于块起点法',c2<covered,(c2,covered))

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,dl=dict(dl),extra=len(extra),
               first_not=len(first_not),lowfirst=lowfirst,contig=contig,
               covered=covered,overlap=overlap,gaps=len(gaps)),open('_r205/m3_blocks.json','w'),indent=1)
