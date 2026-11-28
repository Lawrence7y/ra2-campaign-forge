#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第五刀：ncb 语义的决定性判别（修正 m4 三处方向错）。
m4 自错（全部判据方向写反，无一条进入结论）：
  S6 F1d 步长断言写成 +24；实测同 CHD 内数组元素地址**递减**，步长 -24（m1 的 L[j]-L[j+1]==24 已给出）。
  S7 F3a 断言「最大值在**最后**一个元素」；实测在**第一个**元素（AbstractClass 链 ncb[0]=7=m-1）。
  S8 F2a 断言全部元素 ncb==n-1；实测只有下标 0 满足（954/2615 == 954 个 CHD 恰好各 1 个）。
本刀判别：ncb 是「按位置算的下标逆序」还是「按继承图算的实含基数」，用**同 CHD 内 pTD 是否重复**切开。
C1 数组方向：同 CHD 内相邻 BCD 地址差恒 -24。
C2 ncb[0] == n-1 且 mdisp[0]==0（most-derived 在 [0]）。
C3 分两组测 ncb[j] == n-1-j：
   G-clean = 该 CHD 内 pTD 全不重复；G-rep = 有重复 pTD。
C4 若 G-clean 100% 而 G-rep 不足，则 ncb 的偏离**完全由重复基类（多继承/共享基类）解释**。
C5 ncb 的自反模型：ncb[j] == (该 BCD 的 pTD 对应 COL 所引用 CHD 的 n) - 1，按 mdisp==0 的 COL 取。
C6 反控：把 G-clean 组的下标方向反过来（ncb == j）必须 FAIL。
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
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
OWN={}
for c,cc in COL.items():
    if cc['mdisp']==0: OWN.setdefault(cc['ptd'],cc['pchd'])
ck('C0 语料 COL=1214 / VT=1214 / CHD=954',(len(COL),len(VT),len(CHD))==(1214,1214,954),(len(COL),len(VT),len(CHD)))
# C1
neg=pos=0
for v,d in CHD.items():
    for j in range(d['n']-1):
        if d['bcds'][j+1]-d['bcds'][j]==-24: neg+=1
        elif d['bcds'][j+1]-d['bcds'][j]==24: pos+=1
ck('C1a 同 CHD 相邻 BCD 地址差恒 -24（递减）',neg>0 and pos==0,(neg,pos))
# C2
ok2=0;bad2=[]
for v,d in CHD.items():
    b0=d['bcds'][0]
    if P.dw(b0+4)==d['n']-1 and s32(P.dw(b0+8))==0: ok2+=1
    else: bad2.append((hex(v),P.dw(b0+4),d['n'],s32(P.dw(b0+8))))
ck('C2a ncb[0]==n-1 且 mdisp[0]==0，覆盖全部 CHD',ok2==len(CHD),(ok2,len(CHD)))
if bad2: print('   反例前 6:',bad2[:6])
# C3 分组
gc_t=gc_h=gr_t=gr_h=0; rep_chd=[]
for v,d in CHD.items():
    pt=[P.dw(b) for b in d['bcds']]
    rep=len(set(pt))!=len(pt)
    if rep: rep_chd.append(v)
    for j,b in enumerate(d['bcds']):
        m= P.dw(b+4)==d['n']-1-j
        if rep: gr_t+=1; gr_h+= m
        else:   gc_t+=1; gc_h+= m
print('   C3 G-clean %d/%d ; G-rep %d/%d ; 重复 CHD 数 %d'%(gc_h,gc_t,gr_h,gr_t,len(rep_chd)))
ck('C3a G-clean（pTD 不重复的 CHD）里 ncb==n-1-j 100%',gc_h==gc_t,(gc_h,gc_t))
ck('C3b G-rep（含重复 pTD 的 CHD）里 ncb==n-1-j 不是 100%',gr_h<gr_t,(gr_h,gr_t))
# C5 自反模型
hit5=0;tot5=0;miss5=0
for v,d in CHD.items():
    for b in d['bcds']:
        tot5+=1; ptd=P.dw(b); ncb=P.dw(b+4)
        o=OWN.get(ptd)
        if o is None: miss5+=1; continue
        if ncb==CHD[o]['n']-1: hit5+=1
print('   C5 自反模型命中 %d / %d（own 缺失 %d）'%(hit5,tot5,miss5))
ck('C5a 自反模型命中率 < 100%（不能单独解释）',hit5<tot5,(hit5,tot5))
# C6 反控
bad6=0
for v,d in CHD.items():
    pt=[P.dw(b) for b in d['bcds']]
    if len(set(pt))!=len(pt): continue
    for j,b in enumerate(d['bcds']):
        if P.dw(b+4)==j: bad6+=1
ck('C6a 反控：G-clean 组用 ncb==j（方向反）几乎不成立',bad6<=1,bad6)
# 结论摘要
res=dict(col=len(COL),vt=len(VT),chd=len(CHD),bcd_total=sum(d['n'] for d in CHD.values()),
  direction='descending(-24)', most_derived_index=0,
  clean=(gc_h,gc_t), repeated=(gr_h,gr_t), rep_chd=len(rep_chd),
  selfref=(hit5,tot5,miss5),
  col_mdisp=dict(collections.Counter(c['mdisp'] for c in COL.values())),
  chd_n=dict(collections.Counter(d['n'] for d in CHD.values())))
json.dump(res,open('_r196/m5_ncb2.json','w'),ensure_ascii=False,indent=1)
print('   COL.mdisp:',res['col_mdisp'])
print('   CHD.n 分布:',res['chd_n'])
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
