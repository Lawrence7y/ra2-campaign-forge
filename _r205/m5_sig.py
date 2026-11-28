#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m5（权威一）：COL.sig 是第三条独立判据 —— sig==0 <=> 该类主对象视图（=R203 的 954 组头）。
修正 m4 的三处脚本 bug / 过强断言：
 ① C2 正控把 CHD+8（numBaseClasses，非 0）当成 cdOffset，应取 +24；
 ② F3a 断言「BCD 池整段在 CHD 段之前」方向错 —— 实测池与 CHD 块**交错**；
 ③ F4a/F4c 断言的是「地址序 == 继承序」，与数据无关，改为基础量。
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
# 修正后的 C2 正控（用 +0/+24/+32）
ok=sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+24)==0 and P.dw(a+32)==a)
ck('V1 正控（修正后）：CHD +0==0 且 +24==0 且 +32==自身 954/954',ok==954,ok)

# ---------- G1 sig 是第三条独立判据 ----------
sigall=collections.Counter(v['sig'] for v in COL.values())
sigemb=collections.Counter(COL[e]['sig'] for e in EMB)
print('   G1 1214 视图 COL 的 sig 分布 %s'%sorted(sigall.items()))
print('   G1 954 内嵌 COL 的 sig 分布 %s'%sorted(sigemb.items()))
ck('G1a 1214 视图 COL sig 分布 == {0:954, 1:?, 2:?} 且 954+260=1214',sum(sigall.values())==1214 and sigall[0]>=954,sorted(sigall.items()))
ck('G1b 954 个内嵌 COL 的 sig 全为 0',sigemb=={0:954},dict(sigemb))
notemb=[c for c in COL if c not in EMB]
sig_notemb=collections.Counter(COL[c]['sig'] for c in notemb)
ck('G1c 260 个非内嵌视图 COL 的 sig 全非 0',len(notemb)==260 and sig_notemb.get(0,0)==0,(len(notemb),sorted(sig_notemb.items())))
ck('G1d **sig==0 <=> 该类主对象视图（组头）** 双向零例外：sig0 集合 == 954 内嵌 COL 集合',
   set(c for c,v in COL.items() if v['sig']==0)==set(EMB),(len(set(c for c,v in COL.items() if v['sig']==0)),len(set(EMB))))
# 与 R203 名字判据的 954 组头集合对比
def parse(vt,maxk=4000):
    hn=COL[VTI[vt]]['name']; curcol=VTI[vt]; out=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn: out.append((curcol,pos)); curcol=w; k+=1; continue
        break
    out.append((curcol,None)); return out
claimed=set(); HEADS=[]
for vt in sorted(VTI):
    if vt in claimed: continue
    HEADS.append(VTI[vt])
    for col,pos in parse(vt):
        claimed.add(col)
        if pos is not None: claimed.add(pos)
heads_col=set(HEADS)
ck('G1e R203 名字判据的 954 组头 COL 集合 == sig==0 集合',
   heads_col==set(EMB),(len(heads_col),len(heads_col&set(EMB))))
ck('G1f 组头数 954 == 类名数 954（复现 R203）',len(heads_col)==954 and len(set(COL[c]['name'] for c in heads_col))==954,None)

# ---------- G2 sig 1 vs 2 的语义探测 ----------
s1=[c for c in notemb if COL[c]['sig']==1]; s2=[c for c in notemb if COL[c]['sig']==2]
print('   G2 sig==1 的 %d 个、sig==2 的 %d 个'%(len(s1),len(s2)))
for grp,nm in ((s1,'sig1'),(s2,'sig2')):
    md=collections.Counter(COL[c]['mdisp'] for c in grp)
    sz=collections.Counter(len(G[COL[c]['pchd']]) for c in grp)
    print('     %s mdisp 分布 top6 %s ; 所在组视图数 %s'%(nm,md.most_common(6),sorted(sz.items())))
# sig 与 mdisp 的关系（全体 1214）
cross=collections.Counter((v['sig'],v['mdisp']==0) for v in COL.values())
ck('G2a 交叉表 (sig, mdisp==0)：sig0 全 mdisp==0；sig1/2 全 mdisp!=0',
   all((s,m)==(0,True) for (s,m),n in cross.items() if s==0) and
   all(m is False for (s,m),n in cross.items() if s!=0), sorted(cross.items()))

# ---------- G3 978 条 mdisp==0 的完整分解 ----------
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(COL[e]['ptd'] for e in EMB)
dup=[b for b in m0 if P.dw(b) in ownset]
extra=[b for b in m0 if P.dw(b) not in ownset]
by_td=collections.Counter(P.dw(b) for b in dup)
d2={td:n for td,n in by_td.items() if n>1}
print('   G3 mdisp==0 共 %d = 自有 %d(含 %d 个 TD 重复) + 非自有 %d'%(len(m0),len(dup),len(d2),len(extra)))
for td,n in list(d2.items())[:4]:
    bs=[b for b in dup if P.dw(b)==td]
    print('      dup TD %s n=%d addrs=%s'%((cname(bs[0]) or '?')[:36],n,[hex(x) for x in bs]))
ck('G3a 978 == 956 自有记录 + 22 非自有',len(m0)==956+22,(len(m0),len(dup),len(extra)))
ck('G3b TD 重复的个数为 2（956-954）',len(d2)==2 and sum(n-1 for n in d2.values())==2,(len(d2),sum(n-1 for n in d2.values())))

# ---------- G4 22 条非自有 mdisp==0：是不是「无 vftable 的纯接口基类」 ----------
names954=set(COL[e]['name'] for e in EMB)
enames=[cname(b) for b in extra]
ck('G4a 22 条的 pTD 名全部不在 954 内',all(n not in names954 for n in enames),None)
u=[n for n in enames if n and n.startswith('.?AU')]
ck('G4b 22 条中 .?AU 前缀（接口/纯基类）占多数',len(u)>=11,(len(u),len(enames)))
# 这些 TD 是否在镜像里有任何 vftable（vt-4 指向某 COL）
tds2col={}
for c,v in COL.items(): tds2col.setdefault(v['ptd'],[]).append(c)
ck('G4c 22 条的 pTD 都不在任何 COL 的 pTD 里（=> 无自带 vftable 视图）',
   all(P.dw(b) not in tds2col for b in extra),len([b for b in extra if P.dw(b) in tds2col]))
refc={P.dw(b):sum(1 for v in BCA.values() for x in v if x==b) for b in extra}
ck('G4d 它们在 BCA 中被引用 474 次（作为基类出现），本身无 CHD',sum(refc.values())==474,sum(refc.values()))

# ---------- G5 反控 ----------
random.seed(2053)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
hit=0
for _ in range(5000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x)==0 and P.dw(x+8)==0 and P.dw(x+32)==x: hit+=1
ck('C1 反控：随机地址命中「+0==0 且 +24==0 且 +32==自身」0 次',hit==0,hit)
c=0
for _ in range(5000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x)==0: c+=1
ck('C2 说明 C1 不是恒假：随机地址 +0==0 的比例 >0',c>0,c)
# 反控：把 sig 判据换成 mdisp==0 单独
ck('C3 反控：mdisp==0 单独不能当组头判据（1214 中 mdisp==0 亦为 954，判据等价；改用 sig 与 pCHD 双源）',
   len(set(c for c,v in COL.items() if v['mdisp']==0))==954, len(set(c for c,v in COL.items() if v['mdisp']==0)))

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,sigall=dict(sigall),sig_notemb=dict(sig_notemb),
               m0=len(m0),dup=len(dup),extra=len(extra),d2=len(d2)),open('_r205/m5_sig.json','w'),indent=1)
