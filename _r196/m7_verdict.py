#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第七刀（定稿裁定）：numContainedBases 的字节语义闭链。
m6 自错两条（判据方向/口径错，不进入结论）：
  S9  E3c 把 mdisp 判据写成「严格递增」；实测 698/954 的链含相等相邻项（0,0,0,0 = 无虚基的纯单继承链，
      mdisp 是虚基偏移，全 0 合法）。正确判据是「非递减」。
  S10 E4b 把占位 pTD 链混进分母；实测 34 条例外 100% 落在占位 pTD（"ss violation - no RTTI data!"）链上。

定稿结论（全部字节可复算）：
V1 数组方向：同 CHD 内 BCD 指针逐项 -24，[0] 是 most-derived。
V2 BCD 布局 24 B：+0 pTD / +4 ncb / +8 mdisp / +12 pdisp(恒 -1) / +16 vdisp(恒 0) / +20 attrs(⊆0xB)。
V3 ncb 语义：**ncb == n-1-j（按数组下标的位置逆序）**，在排除占位 pTD 后 100% 成立；
   即 ncb 不是「后代数」也不是「实含基数」，而是「本链剩余元素数」的同义量。
V4 「最外层 ncb 最大」：ncb[0] == n-1 == max(ncb)，954/954 全覆盖。
V5 例外全部可归因：占位 pTD 链 34 条（ncb 偏离位置模型，成因见 V6）。
V6 占位 pTD：+0 == 0x7F9594、+8 是 C 串 "ss violation - no RTTI data!"，共 11 个 pTD / 34 个 BCD 位置。
V7 mdisp 非递减覆盖率的真值（修正 S9）。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
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
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
PH=set()
for v,d in CHD.items():
    for b in d['bcds']:
        td=P.dw(b)
        nm=P.cstr(td+8,80)
        if not (nm and nm.startswith(b'.?A')): PH.add(td)
def isph(b): return P.dw(b) in PH
ck('V0 占位 pTD 11 个（m3/m4 已实测）',len(PH)==11,[hex(x) for x in PH])
# V1
neg=pos=0
for v,d in CHD.items():
    for j in range(d['n']-1):
        dd=d['bcds'][j+1]-d['bcds'][j]
        if dd==-24: neg+=1
        elif dd==24: pos+=1
ck('V1a 同 CHD 内 BCD 指针逐项 -24',neg>0 and pos==0,(neg,pos))
# V2
tot=sum(d['n'] for d in CHD.values())
pd=collections.Counter(s32(P.dw(b+12)) for v,d in CHD.items() for b in d['bcds'])
vd=collections.Counter(s32(P.dw(b+16)) for v,d in CHD.items() for b in d['bcds'])
at=collections.Counter(P.dw(b+20) for v,d in CHD.items() for b in d['bcds'])
ck('V2a pdisp 恒 -1 / vdisp 恒 0 / attrs ⊆ 0xB',set(pd)=={-1} and set(vd)=={0} and all(x&~0xB==0 for x in at),(dict(pd),dict(vd),dict(at)))
# V3 排除占位
hit=tot2=0;bad=[]
for v,d in CHD.items():
    for j,b in enumerate(d['bcds']):
        if isph(b): continue
        tot2+=1
        if P.dw(b+4)==d['n']-1-j: hit+=1
        else: bad.append((hex(v),j,d['n'],hex(P.dw(b)),P.dw(b+4),d['n']-1-j))
print('   V3 非占位样本 %d 条，ncb==n-1-j 命中 %d'%(tot2,hit))
if bad: print('   反例:',bad[:8])
ck('V3a 排除占位 pTD 后 ncb==n-1-j 100% 成立',hit==tot2,(hit,tot2))
# V3b 占位链的 ncb 是否也满足某模型
ph_hit=ph_tot=0
for v,d in CHD.items():
    for j,b in enumerate(d['bcds']):
        if not isph(b): continue
        ph_tot+=1
        if P.dw(b+4)==d['n']-1-j: ph_hit+=1
print('   V3b 占位链 ncb==n-1-j 命中 %d / %d'%(ph_hit,ph_tot))
ck('V3b 占位链不满足位置模型（故单列）',ph_hit<ph_tot,(ph_hit,ph_tot))
# V4
ok4=0
for v,d in CHD.items():
    ncbs=[P.dw(b+4) for b in d['bcds']]
    if ncbs[0]==d['n']-1 and ncbs[0]==max(ncbs): ok4+=1
ck('V4a ncb[0]==n-1==max(ncb) 覆盖全部 CHD',ok4==len(CHD),(ok4,len(CHD)))
# V6
phb=sum(1 for v,d in CHD.items() for b in d['bcds'] if isph(b))
ck('V6a 占位 pTD 的 +0 全指 0x7F9594',all(P.dw(x)==0x7F9594 for x in PH),(len(PH),))
ck('V6b 占位 pTD +8 是 C 串 ss violation',all((P.cstr(x+8,80) or b'').startswith(b'ss violation') for x in PH),len(PH))
print('   V6 占位 BCD 位置数 =',phb)
# V7 mdisp 非递减
nd=0;nd_bad=[]
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    if all(md[i]<=md[i+1] for i in range(len(md)-1)): nd+=1
    else: nd_bad.append((hex(v),md))
ck('V7a mdisp 非递减覆盖 >=99% 的 CHD',nd>=0.99*len(CHD),(nd,len(CHD)))
for x in nd_bad[:10]: print('   非递减反例:',x)
# 汇总
res=dict(chd=len(CHD),bcd_total=tot,placeholder_td=len(PH),placeholder_bcd=phb,
  pos_model=(hit,tot2),ph_model=(ph_hit,ph_tot),ncb0=(ok4,len(CHD)),
  mono_ok=nd,mono_bad=len(nd_bad),pdisp=dict(pd),vdisp=dict(vd),attrs=dict(at),
  chd_attr=dict(collections.Counter(P.dw(v+4) for v in CHD)))
json.dump(res,open('_r196/m7_verdict.json','w'),ensure_ascii=False,indent=1)
print('   CHD.attr:',res['chd_attr'])
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
