# -*- coding: utf-8 -*-
"""R211 c21（收口）：律 W 与 R210 律 U 的域对齐。
c20 的 a1/b1 判据错在：COL 记录的 +12 是「本类 own TD」，不是 BCD 的接口 pTD，故 (pTD,mdisp) 天然不配对。
修正后检验：
  T1 T 形态视图（mdisp ∈ {4,24,36,40,44,1728} 且 slots0-2 全为 thunk）的偏移集合
     == BCA 中 pTD 名以 .?AU 开头的记录的 mdisp 集合 - {0}
     （这就是律 U 的 {4}∪R，且给出 {4} 的机制：它来自 ?AUIRTTITypeInfo/?AUIUnknown 记录）
  T2 S 形态视图（mdisp ∈ {8,12,21784}）的偏移集合 == BCA 中 pTD ∈ TD_OWN 且名以 .?AV 开头的记录的 mdisp 集合
  T3 两者并集 == 律 W 的 V_all
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(addr=base+4*i,sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={a:[COL[c] for c in G[a] if c==a+16][0] for a in CHD}
TDOWN=set(v['pTD'] for v in own.values())
Vall={a:set(COL[c]['mdisp'] for c in G[a])-{0} for a in CHD}
NM={a:own[a]['name'] for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
# 形态归类：R210 QS5 交叉表 4/24/36/40/44/1728→T ; 8/12/21784→S
TF={4,24,36,40,44,1728}; SF={8,12,21784}
VT_T={}; VT_S={}; VT_I={}
for a in CHD:
    VT_T[a]=set(x for x in Vall[a] if x in TF)
    VT_S[a]=set(x for x in Vall[a] if x in SF)
    VT_I[a]=set(x for x in Vall[a] if x not in TF and x not in SF)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
print('=== 形态归类（T/S/I 按 mdisp 值，取自 R210 QS5 交叉表）===')
print('  T 域类数=%d  S 域类数=%d  I(既非T非S)=%d'%(sum(1 for a in CHD if VT_T[a]),sum(1 for a in CHD if VT_S[a]),sum(1 for a in CHD if VT_I[a])))
print('  I 域出现的 mdisp 值：%s'%sorted(set(x for a in CHD for x in VT_I[a])))
# T1
def pred_U(a):
    return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and tdn(r['pTD']).startswith('.?AU'))
def pred_S(a):
    return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and r['pTD'] in TDOWN and tdn(r['pTD']).startswith('.?AV'))
def pred_W(a):
    return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN))
b1=[a for a in CHD if pred_U(a)!=VT_T[a]]
ck('T1 V_T(c) == {mdisp | pTD 名 .?AU}', len(b1)==0,'失配 %d / 954'%len(b1))
for a in b1[:6]: print('     %-34s V_T=%s pred=%s'%(NM[a],sorted(VT_T[a]),sorted(pred_U(a))))
b2=[a for a in CHD if pred_S(a)!=VT_S[a]]
ck('T2 V_S(c) == {mdisp | pTD∈TD_OWN ∧ 名 .?AV}', len(b2)==0,'失配 %d / 954'%len(b2))
for a in b2[:6]: print('     %-34s V_S=%s pred=%s'%(NM[a],sorted(VT_S[a]),sorted(pred_S(a))))
b3=[a for a in CHD if pred_W(a)!=Vall[a]]
ck('T3 V_all(c) == 律 W', len(b3)==0,'失配 %d / 954'%len(b3))
# T4: 律 W 是否等于 T1 ∪ T2 逐类
b4=[a for a in CHD if (pred_U(a)|pred_S(a))!=Vall[a]]
ck('T4 律 W == T1 ∪ T2 逐类（零残留）', len(b4)==0,'失配 %d / 954'%len(b4))
# T5: HouseClass 三分解
a=0x802a18
print('\n=== HouseClass 三分解 ===')
print('  V_all=%s'%sorted(Vall[a]))
print('  V_T  =%s  ← 律 U 公式结果，R210 报的 {4}∪{36,40,44}'%sorted(VT_T[a]))
print('  V_S  =%s'%sorted(VT_S[a]))
print('  律W  =%s'%sorted(pred_W(a)))
print('  T1 预测 V_T=%s ; T2 预测 V_S=%s'%(sorted(pred_U(a)),sorted(pred_S(a))))
print('  ⇒ R210 把 V_all 当成律 U 的域是口径问题：8/12 属 S 形态（.?AVINoticeSink / .?AVINoticeSource），不在律 U 域内')
ck('T5 HouseClass V_T == {4,36,40,44}', VT_T[a]=={4,36,40,44}, sorted(VT_T[a]))
# T6 全局：T 域 mdisp 值只可能来自 ?AU
val_src=collections.defaultdict(collections.Counter)
for c in CHD:
    for r in ALLR[c]:
        if r['mdisp']==0: continue
        val_src[r['mdisp']]['U' if tdn(r['pTD']).startswith('.?AU') else ('Vown' if r['pTD'] in TDOWN else 'Vother')]+=1
print('\n=== mdisp 值 → 记录来源 ===')
for m in sorted(val_src): print('  mdisp=%-7d %s'%(m,dict(val_src[m])))
ck('T6 T 域 6 个 mdisp 值只来自 ?AU 记录', all(set(val_src[m])=={'U'} for m in TF), {m:dict(val_src[m]) for m in sorted(TF)})
ck('T7 S 域 3 个 mdisp 值只来自 TD_OWN 的 ?AV 记录', all(set(val_src[m])=={'Vown'} for m in SF), {m:dict(val_src[m]) for m in sorted(SF)})
json.dump({'T_fail':len(b1),'S_fail':len(b2),'W_fail':len(b3),'union_fail':len(b4),
 'house_T':sorted(VT_T[a]),'house_S':sorted(VT_S[a]),'house_all':sorted(Vall[a]),
 'val_src':{str(m):dict(val_src[m]) for m in sorted(val_src)},
 'T_domain':sorted(TF),'S_domain':sorted(SF),'classes':len(CHD)},
 open('/home/t628/projects/ra2-campaign-forge/_r211/c21.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
