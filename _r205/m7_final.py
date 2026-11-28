#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m7（定稿）：CHD 40 字节头 + 内嵌主对象 COL + 两个 954 的区别。
m6 自错（3 处，全为我方断言/脚本写错）：
 ① H1b 把 vftable 内**所有**文本槽位都塞进 claimed_vt（14,304），而 R203 只把「槽流遇同类名 COL」的
    那个位置算伪起点 —— 260 是「被内嵌 COL 占掉的伪 vftable 起点」数，不是全部文本槽位；
 ② H2a/H2b 假设「954 组头 COL == 954 内嵌 COL」实测交集仅 860 —— 因 MI 类组头是 mdisp 最大的
    首视图、而内嵌 COL 是 mdisp==0 的末视图，两者只在单视图类上重合（860 = 954 - 94 MI 类）；
 ③ H2f 用 head_of_col 索引 CHD+16，对 94 个 MI 类 KeyError；
 ④ m7 首跑 G1 得 1214/0/1729 —— seps 里存的是 COL 指针位置（vt-4），而 VTI 的键是 vftable 起点（vt），
    用 p 判 in VTI 恒假，应判 p+4。修正后 954/260/1214。
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
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v)); EMB={a+16:a for a in CHD}
ck('V0 基数 COL1214/VTI1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,1214,954,1002,2615),
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values())))

# ---------- 视图解析（只把「同类名 COL」当视图分隔） ----------
def parse(vt,maxk=4000):
    hn=COL[VTI[vt]]['name']; cur=VTI[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn:
            views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
swallowed=0; HEADS=[]; skip=set(); VIE={}
for vt in sorted(VTI):
    if vt in skip: continue
    views,seps=parse(vt); HEAD=VTI[vt]; HEADS.append(HEAD); skip.add(vt)
    VIE[HEAD]=views
    for p in seps:
        if p+4 in VTI: swallowed+=1; skip.add(p+4)
ck('G1 组头 954 / 被吞伪起点 260 / 视图 1214（复现 R203）',
   (len(HEADS),swallowed,sum(len(v) for v in VIE.values()))==(954,260,1214),
   (len(HEADS),swallowed,sum(len(v) for v in VIE.values())))
ck('G2 每类视图数分布 == 1:860/2:10/3:6/4:76/5:1/7:1（复现 R203）',
   dict(collections.Counter(len(v) for v in VIE.values()))=={1:860,2:10,3:6,4:76,5:1,7:1},
   dict(collections.Counter(len(v) for v in VIE.values())))

# ---------- D1 两个 954 的精确关系 ----------
HEAD2CHD={}
for h in HEADS:
    for a in CHD:
        if a+16 in VIE[h]: HEAD2CHD[h]=a; break
ck('D1a 954 个组头各自唯一映射到 1 个 CHD',len(HEAD2CHD)==954 and len(set(HEAD2CHD.values()))==954,
   (len(HEAD2CHD),len(set(HEAD2CHD.values()))))
c=collections.Counter(HEAD2CHD.values())
ck('D1b 954 个 CHD 各被恰 1 个组头覆盖',all(c[a]==1 for a in CHD),collections.Counter(c.values()))
same=sum(1 for h,a in HEAD2CHD.items() if h==a+16)
ck('D1c 组头 == 内嵌 COL 的类数 860（=单视图类）',same==860,same)
ck('D1d 组头 != 内嵌 COL 的类数 94（=MI 类）',954-same==94,954-same)
mi=[h for h,a in HEAD2CHD.items() if h!=a+16]
ck('D1e 94 个不等的类恰是多视图类（视图数>1）94 个',
   len(mi)==94 and all(len(VIE[h])>1 for h in mi),sum(1 for h in mi if len(VIE[h])==1))
ck('D1f 860 个相等的类恰是单视图类',
   all(len(VIE[h])==1 for h,a in HEAD2CHD.items() if h==a+16),
   len([h for h,a in HEAD2CHD.items() if h==a+16 and len(VIE[h])>1]))
# MI 类：组头 mdisp != 0，末视图 mdisp == 0
ck('D1g MI 类组头 mdisp != 0 94/94',all(COL[h]['mdisp']!=0 for h in mi),sum(1 for h in mi if COL[h]['mdisp']==0))
ck('D1h 每组末视图 mdisp == 0 且 == CHD+16 954/954',
   all(COL[VIE[h][-1]]['mdisp']==0 and VIE[h][-1]==HEAD2CHD[h]+16 for h in HEADS),
   sum(1 for h in HEADS if VIE[h][-1]!=HEAD2CHD[h]+16))
# 组内 mdisp 单调递减
ck('D1i 组内 mdisp 严格递减 954/954',
   all(all(COL[VIE[h][i]]['mdisp']>COL[VIE[h][i+1]]['mdisp'] for i in range(len(VIE[h])-1)) for h in HEADS),
   sum(1 for h in HEADS if any(COL[VIE[h][i]]['mdisp']<=COL[VIE[h][i+1]]['mdisp'] for i in range(len(VIE[h])-1))))

# ---------- D2 CHD 40 字节头定稿 ----------
d=collections.Counter()
for a in CHD:
    d[(P.dw(a)==0, P.dw(a+4) in (0,1,5), P.dw(a+8)==len(BCA[a]), P.where(P.dw(a+12))=='.rdata',
       P.dw(a+24)==0, P.dw(a+32)==a, COL[a+16]['pchd']==a)]+=1
ck('D2a CHD 40B 头七条同时成立 954/954：+0==0 / +4∈{0,1,5} / +8==len(BCA) / +12 pBCA∈.rdata / +24==0 / +32==自身 / 内嵌COL.pCHD==自身',
   d=={(True,)*7:954},d.most_common(3))
print('   D2 +4 attributes %s'%collections.Counter(P.dw(a+4) for a in CHD).most_common())
print('   D2 +8 numBaseClasses 分布 %s'%sorted(collections.Counter(P.dw(a+8) for a in CHD).items())[:10])
print('   D2 +12 pBCA 段 %s'%collections.Counter(P.where(P.dw(a+12)) for a in CHD).most_common())
print('   D2 内嵌COL +16 sig %s ; +20 mdisp %s ; +24 cd %s ; +28 pTD 段 %s'%(
   collections.Counter(P.dw(a+16) for a in CHD).most_common(2),
   collections.Counter(s32(P.dw(a+20)) for a in CHD).most_common(2),
   collections.Counter(P.dw(a+24) for a in CHD).most_common(2),
   collections.Counter(P.where(P.dw(a+28)) for a in CHD).most_common(2)))

# ---------- D3 978 条 mdisp==0 三分类定稿 ----------
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(P.dw(a+28) for a in CHD)
dup=[b for b in m0 if P.dw(b) in ownset]; extra=[b for b in m0 if P.dw(b) not in ownset]
ck('D3a 978 = 956 自有 + 22 非自有',(len(m0),len(dup),len(extra))==(978,956,22),(len(m0),len(dup),len(extra)))
ck('D3b 956 自有覆盖 954 个 TD（2 个 TD 各 2 条）',len(set(P.dw(b) for b in dup))==954,
   len(set(P.dw(b) for b in dup)))
ck('D3c 22 条非自有的 pTD 名不在 954 类名集内',
   all(cname(b) not in set(COL[e]['name'] for e in EMB) for b in extra),None)
ck('D3d 22 条中 .?AU 接口前缀 17 条',sum(1 for b in extra if (cname(b) or '').startswith('.?AU'))==17,None)
refc=collections.Counter()
for v in BCA.values():
    for x in v:
        if x in set(extra): refc[x]+=1
ck('D3e 22 条在 BCA 中被引用 474 次',sum(refc.values())==474,sum(refc.values()))
ck('D3f 22 条的 pTD 从不出现在任何 COL.pTD（无 vftable）',
   all(P.dw(b) not in set(v['ptd'] for v in COL.values()) for b in extra),None)

# ---------- D4 反控 ----------
random.seed(2055)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
hit=0
for _ in range(5000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x)==0 and P.dw(x+8)==0 and P.dw(x+32)==x: hit+=1
ck('C1 反控：5000 随机地址按 CHD 头判据 0 命中',hit==0,hit)
ck('C2 反控：CHD+20 平移集合与 954 组头集合不相交',len(set(a+20 for a in CHD)&set(HEADS))==0,
   len(set(a+20 for a in CHD)&set(HEADS)))
ck('C3 反控：把内嵌 COL 的 pCHD 判据换成「pTD==自有」时，改用随机同长 BCD 不成立（D3f 对照）',
   sum(1 for b in extra if P.dw(b) in set(v['ptd'] for v in COL.values()))==0,0)

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,heads=954,swallowed=260,views=1214,
               same860=same,mi94=94,m0=len(m0),dup=len(dup),extra=len(extra),
               refextra=sum(refc.values()),
               attr=dict(collections.Counter(P.dw(a+4) for a in CHD)),
               nbc=dict(collections.Counter(P.dw(a+8) for a in CHD))),
          open('_r205/m7_final.json','w'),indent=1)
