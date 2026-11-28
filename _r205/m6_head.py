#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m6（权威二）：修正组头解析 + 交付「内嵌主对象 COL」与 R203 组头一一对应。
m5 自错（4 处，全部为我方断言/脚本写错，数据无异常）：
 ① G1a/G2a 假设 COL.sig ∈ {0,1,2} 有区分力 —— 实测**全 1214 条 sig 均为 0**，该字段在本镜像无判别力（否定结果）；
 ② G1c/G1d/G1e 由此连锁失效；
 ③ G1f 的 claimed 集合混装 COL 地址与 vftable 地址（claimed.add(col) 却用 vt in claimed 判断），
    导致 1214 个 vftable 全部被当组头（len(HEADS_COL)==1214 而非 954）；
 ④ G4d 用 dict 以 TD 为键统计引用，两个 TD 各被 2 条 BCD 共用时被折叠（474 -> 376）。
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
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
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
EMB={a+16:a for a in CHD}
ck('V0 基数 COL1214/VTI1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,1214,954,1002,2615),
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values())))
ck('V1 sig 全 1214 恒 0（否定结果，本字段无判别力）',set(v['sig'] for v in COL.values())=={0},sorted(set(v['sig'] for v in COL.values())))

# ---------- H1 修正后的组头解析（claimed 只装 COL 地址，与 vt 分开） ----------
def parse_views(vt, maxk=4000):
    hn=COL[VTI[vt]]['name']; curcol=VTI[vt]; views=[]; positions=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): positions.append(pos); k+=1; continue
        if w in COL and COL[w]['name']==hn:
            views.append(curcol); positions.append(pos); curcol=w; k+=1; continue
        break
    views.append(curcol); return views, positions
claimed_col={}          # COL 地址 -> 组头 COL
claimed_vt={}           # 被内嵌 COL 占掉的 vftable 伪起点
HEADS=[]
for vt in sorted(VTI):
    if vt in claimed_vt: continue
    views,positions=parse_views(vt)
    HEADS.append(VTI[vt])
    for idx,c in enumerate(views):
        claimed_col[c]=VTI[vt]
    for p in positions:
        claimed_vt[p]=vt
ck('H1a 组头数 954',len(HEADS)==954,len(HEADS))
ck('H1b 被吞的 vftable 伪起点 260',len(claimed_vt)==260,len(claimed_vt))
ck('H1c 组头 COL 互异 954',len(set(HEADS))==954,len(set(HEADS)))
ck('H1d 覆盖全部 1214 个视图 COL',len(claimed_col)==1214,len(claimed_col))
ck('H1e 组头 COL 数 954 == 不同类名数 954',
   len(set(HEADS))==954 and len(set(COL[c]['name'] for c in HEADS))==954,
   (len(set(HEADS)),len(set(COL[c]['name'] for c in HEADS))))
# 视图数分布
vc=collections.Counter(claimed_col.values())
ck('H1f 每类视图数分布 == R203 1:860/2:10/3:6/4:76/5:1/7:1',
   dict(collections.Counter(vc.values()))=={1:860,2:10,3:6,4:76,5:1,7:1},
   dict(collections.Counter(vc.values())))

# ---------- H2 核心：954 个组头 COL == 954 个 CHD+16 内嵌 COL ----------
ck('H2a 组头 COL 集合 == CHD+16 内嵌 COL 集合（第三条独立判据）',
   set(HEADS)==set(EMB),(len(set(HEADS)&set(EMB)),len(set(HEADS)|set(EMB))))
# 逐组：组内 mdisp==0 的视图恰为组头
zper=collections.Counter()
for c,h in claimed_col.items():
    if COL[c]['mdisp']==0: zper[h]+=1
ck('H2b 每组恰 1 个 mdisp==0 的视图，且就是组头 954/954',
   all(zper[h]==1 and COL[h]['mdisp']==0 for h in HEADS),collections.Counter(zper.values()))
# 逐 CHD：mdisp==0 的唯一视图 COL 就是 a+16（复现 m2 D2b）
ck('H2c 每 CHD 的 mdisp==0 视图 COL == CHD+16 954/954',
   all([c for c in G[a] if COL[c]['mdisp']==0]==[a+16] for a in CHD),None)
# 组头 -> 主 vftable 起点（vt-4 == 组头 COL）
vt_of_col={c:vt for vt,c in VTI.items()}
ck('H2d 954 组头每个都有主 vftable（vt-4 == 组头 COL）954/954',
   all(h in vt_of_col for h in HEADS),sum(1 for h in HEADS if h not in vt_of_col))
MAINVT={a:vt_of_col[a+16] for a in CHD}
ck('H2e 954 个主 vftable 起点互异',len(set(MAINVT.values()))==954,len(set(MAINVT.values())))
head_of_col={}
for h in HEADS:
    for c,hh in claimed_col.items():
        if hh==h: head_of_col[h]=vt_of_col[h]
ck('H2f 954 个主 vftable 起点与 954 个组头一一对应',
   all(vt_of_col[a+16]==head_of_col[a+16] for a in CHD),None)

# ---------- H3 40 字节头逐字段（最终定稿值） ----------
f=collections.Counter()
for a in CHD:
    f[('+0',P.dw(a))]+=1; f[('+4',P.dw(a+4))]+=1; f[('+24',P.dw(a+24))]+=1
d=collections.Counter()
for a in CHD: d[(P.dw(a)==0, P.dw(a+4) in (0,1,5), P.dw(a+24)==0, P.dw(a+32)==a)]+=1
ck('H3a CHD 40 字节头：+0 恒 0 / +4 ∈{0,1,5} / +24 恒 0 / +32 pCHD==自身 954/954',
   d=={(True,True,True,True):954},d.most_common(3))
print('   H3 +4(attributes) 分布 %s'%collections.Counter(P.dw(a+4) for a in CHD).most_common())
print('   H3 +8(numBaseClasses) 分布 top6 %s'%collections.Counter(P.dw(a+8) for a in CHD).most_common(6))
ck('H3b +8 == len(BCA) 954/954',all(P.dw(a+8)==len(BCA[a]) for a in CHD),None)
ck('H3c +12 == pBCA 且全在 .rdata 954/954',
   all(P.where(P.dw(a+12))=='.rdata' for a in CHD),collections.Counter(P.where(P.dw(a+12)) for a in CHD).most_common())
print('   H3 +28(内嵌 COL.pTD) 全在 .data? %s'%collections.Counter(P.where(P.dw(a+28)) for a in CHD).most_common())

# ---------- H4 978 条 mdisp==0 的最终分解 ----------
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(P.dw(a+28) for a in CHD)
dup=[b for b in m0 if P.dw(b) in ownset]
extra=[b for b in m0 if P.dw(b) not in ownset]
ck('H4a 978 = 956 自有 + 22 非自有（.data 记录）',(len(m0),len(dup),len(extra))==(978,956,22),(len(m0),len(dup),len(extra)))
ck('H4b 956 自有 = 954 类 + 2 个重复 TD',len(set(P.dw(b) for b in dup))==954,len(set(P.dw(b) for b in dup)))
refc=collections.Counter()
for v in BCA.values():
    for x in v:
        if x in set(extra): refc[x]+=1
ck('H4c 22 条非自有在 BCA 中被引用 474 次（作为无 vftable 基类）',sum(refc.values())==474,sum(refc.values()))
ck('H4d 22 条的 pTD 名不在 954 类名集合内',all(cname(b) not in set(COL[e]['name'] for e in EMB) for b in extra),None)
ck('H4e 22 条中 .?AU 接口前缀 17 条',sum(1 for b in extra if (cname(b) or '').startswith('.?AU'))==17,
   sum(1 for b in extra if (cname(b) or '').startswith('.?AU')))

# ---------- H5 反控 ----------
random.seed(2054)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
hit=0
for _ in range(5000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x)==0 and P.dw(x+8)==0 and P.dw(x+32)==x: hit+=1
ck('C1 反控：5000 随机地址按 CHD 头判据命中 0',hit==0,hit)
# 反控：把 CHD+16 平移 +4 后组头集合是否仍与内嵌集合相等
alt=set(a+20 for a in CHD)
ck('C2 反控：CHD+20 平移集合与组头集合不相交',len(alt & set(HEADS))==0,len(alt & set(HEADS)))
# 反控：只用 pCHD 分组推出的「mdisp==0 视图」是否也是 954（说明 H2c 与分组自洽但不恒真）
z=set(c for c,v in COL.items() if v['mdisp']==0)
ck('C3 说明：1214 中 mdisp==0 恰 954 —— 与 sig 不同，mdisp 有判别力',len(z)==954,len(z))

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,heads=len(HEADS),swallowed=len(claimed_vt),
               viewdist=dict(collections.Counter(vc.values())),
               m0=len(m0),dup=len(dup),extra=len(extra),refextra=sum(refc.values()),
               attr=dict(collections.Counter(P.dw(a+4) for a in CHD)),
               nbc=dict(collections.Counter(P.dw(a+8) for a in CHD).most_common(8))),
          open('_r205/m6_head.json','w'),indent=1)
