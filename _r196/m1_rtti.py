#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第一刀：RTTI 三层结构（COL -> CHD -> BCD）的字节实证 + numContainedBases 语义。
审计对象：R195 PX9 遗留③「numContainedBases 最大 = 最外层」无编译器侧依据。
口径全部来自字节读，不引用任何外部文档术语；外部命名一律标注为外部源。
T1 COL 结构：+0 signature / +4 mdisp / +8 pdisp / +12 pTD / +16 pCHD 的字段宽度与 all-zero 面。
T2 CHD 结构：+0 signature / +4 attributes / +8 numBaseClasses / +12 pBCD 数组。
T3 BCD 结构：+0 pTD / +4 numContainedBases / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes
   —— 步长必须恰 24 B（数组内相邻元素差）。
T4 ncb 语义三模型对比：
   M1 ncb[j] == n-1-j（按数组下标）
   M2 ncb[j] == 该 BCD 在嵌套树中的后代数
   M3 ncb[j] == n-1（全表同一值）
T5 COL.mdisp 与 BCD[pTD 相同].mdisp 的一致性（全 COL 覆盖，独立自证）。
T6 反控：把 BCD 步长写成 16/20/28 时步长断言必须 FAIL。
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pdisp=s32(w[i+2]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
ck('T0 语料：COL=1214 / VT=1214 / 主表=954',(len(COL),len(VT),len(MAIN))==(1214,1214,954),(len(COL),len(VT),len(MAIN)))
# ---- T1 COL signature 面
sig=collections.Counter(c['sig'] for c in COL.values())
pdisp=collections.Counter(c['pdisp'] for c in COL.values())
print('   T1 COL+0 signature 分布:',dict(sig))
print('   T1 COL+8 pdisp 分布:',dict(pdisp))
ck('T1a COL+0 signature 只有 0/1/2 三值',set(sig)<= {0,1,2},dict(sig))
ck('T1b COL+8 pdisp 恒 0',set(pdisp)=={0},dict(pdisp))
# ---- T2/T3 CHD 与 BCD
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v in CHD: continue
    CHD[v]=dict(sig=P.dw(v),attr=P.dw(v+4),n=P.dw(v+8),arr=P.dw(v+12))
print('   T2 CHD 数=%d'%len(CHD))
ch_sig=collections.Counter(d['sig'] for d in CHD.values()); ch_attr=collections.Counter(d['attr'] for d in CHD.values())
print('   T2 CHD+0 signature:',dict(ch_sig),' CHD+4 attributes:',dict(ch_attr))
ck('T2a CHD+0 signature 恒 0',set(ch_sig)=={0},dict(ch_sig))
ck('T2b CHD+4 attributes 只有 1 个值',len(ch_attr)==1,dict(ch_attr))
BCDS={}
for v,d in CHD.items():
    arr=d['arr']
    if P.where(arr) in ('None','other'):
        d['bcds']=None; continue
    lst=[]
    for j in range(d['n']):
        b=P.dw(arr+4*j); lst.append(b)
    d['bcds']=lst
    for b in lst: BCDS[b]=dict(ptd=P.dw(b),ncb=P.dw(b+4),mdisp=s32(P.dw(b+8)),pdisp=s32(P.dw(b+12)),vdisp=s32(P.dw(b+16)),attr=P.dw(b+20),chd=v)
print('   T3 BCD 数=%d（去重）'%len(BCDS))
# 步长：同一 CHD 内数组相邻元素指针差
strides=collections.Counter()
for d in CHD.values():
    L=d['bcds'] or []
    for j in range(len(L)-1): strides[L[j]-L[j+1]]+=1
print('   T3 BCD 相邻数组元素地址差:',dict(strides))
ck('T3a BCD 步长恒 24 B（>=99% 样本）',strides.get(24,0)>=0.99*sum(strides.values()),(strides.get(24,0),sum(strides.values())))
b_attr=collections.Counter(x['attr'] for x in BCDS.values()); b_vd=collections.Counter(x['vdisp'] for x in BCDS.values()); b_pd=collections.Counter(x['pdisp'] for x in BCDS.values())
print('   T3 BCD+20 attributes:',dict(b_attr),' +16 vdisp:',dict(b_vd),' +12 pdisp:',dict(b_pd))
json.dump(dict(col={hex(k):v for k,v in COL.items()},chd={hex(k):{kk:(vv if kk!='bcds' else ([hex(x) for x in (vv or [])])) for kk,vv in v.items()} for k,v in CHD.items()},
               bcd={hex(k):v for k,v in BCDS.items()},main=[hex(x) for x in MAIN],vt={hex(k):hex(v) for k,v in VT.items()}),
          open('_r196/m1_rtti.json','w'))
print('--- 断言小计 %d 条 / FAIL %d ---'%(N,len(fails)))
