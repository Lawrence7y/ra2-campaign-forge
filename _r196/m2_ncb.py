#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第二刀（定稿）：numContainedBases 的字节语义 —— 补 R195 PX9 遗留③。
m1 的两条 FAIL 是判据写法错误（已记录为自错 S1/S2）：
  S1 把 BaseClassArray 当成内联 24 B 元素数组去量步长；实测元素是**指针**，指针差无意义。
  S2 断言 CHD+4 attributes 恒等；实测 {0:855, 1:66, 5:33}，值域合法（bit0 / bit2）。
本刀改用「字段级不变量」而不依赖地址相邻性。
N1 BCD 结构 24 B：+0 pTD / +4 ncb / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes。
   断言 pdisp 恒 -1、vdisp 恒 0、attributes bit 集 ⊆ {bit0, bit3}。
N2 TypeDescriptor 形态：+0 指向 .rdata、+4 == 0、+8 是 .?A..@@ 名字。
N3 ncb 语义模型（三种，全部可被数据否掉）：
   M1 位置模型  ncb[j] == n-1-j
   M2 自反模型  ncb[j] == CHD(own(BCD[j].pTD)).n - 1，own 取该 pTD 的 mdisp==0 的 COL
   M3 常量模型  ncb[j] == n-1
N4 「最外层」字节判据：ncb[0] == n-1 且 ncb[0] == max(ncb[0..n-1])，覆盖全部 CHD。
N5 COL.mdisp == BCD(该 pTD 在其 CHD 内).mdisp；COL.sig == 该 BCD 的数组下标序号面。
N6 反控：把 own() 换成「任意同 pTD 的 COL（含 mdisp!=0）」时 M2 必须掉下来。
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
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pdisp=s32(w[i+2]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v in CHD: continue
    CHD[v]=dict(sig=P.dw(v),attr=P.dw(v+4),n=P.dw(v+8),arr=P.dw(v+12),bcds=[])
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
BCDS={}
for v,d in CHD.items():
    for j,b in enumerate(d['bcds']):
        BCDS[b]=dict(ptd=P.dw(b),ncb=P.dw(b+4),mdisp=s32(P.dw(b+8)),pdisp=s32(P.dw(b+12)),vdisp=s32(P.dw(b+16)),attr=P.dw(b+20),chd=v,idx=j)
# pTD -> mdisp==0 的 COL（own），以及全部 COL 列表
OWN={};ALLPTD=collections.defaultdict(list)
for c,cc in COL.items():
    ALLPTD[cc['ptd']].append(c)
    if cc['mdisp']==0: OWN.setdefault(cc['ptd'],c)
ck('N0 语料：COL 1214 / CHD 954 / BCD 去重 1002',(len(COL),len(CHD),len(BCDS))==(1214,954,1002),(len(COL),len(CHD),len(BCDS)))
# N1
pd=collections.Counter(x['pdisp'] for x in BCDS.values()); vd=collections.Counter(x['vdisp'] for x in BCDS.values())
at=collections.Counter(x['attr'] for x in BCDS.values())
print('   N1 pdisp:',dict(pd),' vdisp:',dict(vd),' attributes:',dict(at))
ck('N1a BCD+12 pdisp 恒 -1',set(pd)=={-1},dict(pd))
ck('N1b BCD+16 vdisp 恒 0',set(vd)=={0},dict(vd))
ck('N1c BCD+20 attributes bit 集 ⊆ {bit0,bit3}',all(v & ~0x9 == 0 for v in at),dict(at))
ch_attr=collections.Counter(d['attr'] for d in CHD.values())
ck('N1d CHD+4 attributes bit 集 ⊆ {bit0,bit2}',all(v & ~0x5 == 0 for v in ch_attr),dict(ch_attr))
# N2
bad_td=[];tdform=collections.Counter()
for b,x in BCDS.items():
    td=x['ptd']; v0=P.dw(td); v1=P.dw(td+4); nm=P.cstr(td+8,80)
    ok = P.where(v0)=='.rdata' and v1==0 and nm and nm.startswith(b'.?A') and nm.endswith(b'@@')
    tdform[ok]+=1
    if not ok: bad_td.append(b)
ck('N2a 全部 1002 个 pTD 形态合法（+0 指 .rdata / +4=0 / +8 是类名）',not bad_td,(tdform.get(True),tdform.get(False)))
# N3 三模型
n_bcd_total=0
M1=M2=M3=0
ncb_max_is_n_minus_1=0; ncb0_is_n_minus_1=0; ncb0_is_max=0
chd_cnt=0
miss_own=[]
for v,d in CHD.items():
    n=d['n']; lst=d['bcds']; chd_cnt+=1
    ncbs=[P.dw(b+4) for b in lst]
    if ncbs:
        if ncbs[0]==n-1: ncb0_is_n_minus_1+=1
        if ncbs[0]==max(ncbs): ncb0_is_max+=1
    for j,b in enumerate(lst):
        n_bcd_total+=1
        ncb=ncbs[j]
        if ncb==n-1-j: M1+=1
        if ncb==n-1: M3+=1
        o=OWN.get(P.dw(b))
        if o is None: miss_own.append(b); continue
        if ncb==CHD[COL[o]['pchd']]['n']-1: M2+=1
print('   N3 样本 %d ; M1(位置)=%d ; M2(自反)=%d ; M3(常量)=%d ; own 缺失 %d'%(n_bcd_total,M1,M2,M3,len(miss_own)))
ck('N3a M2 自反模型 100% 命中',M2==n_bcd_total,(M2,n_bcd_total))
ck('N3b M1 位置模型 != 100%（应被否）',M1<n_bcd_total,(M1,n_bcd_total))
ck('N3c M3 常量模型 != 100%（应被否）',M3<n_bcd_total,(M3,n_bcd_total))
# N4
print('   N4 CHD %d 张 ; ncb[0]==n-1 : %d ; ncb[0]==max : %d'%(chd_cnt,ncb0_is_n_minus_1,ncb0_is_max))
ck('N4a ncb[0]==n-1 全覆盖',ncb0_is_n_minus_1==chd_cnt,(ncb0_is_n_minus_1,chd_cnt))
ck('N4b ncb[0]==max(ncb) 全覆盖',ncb0_is_max==chd_cnt,(ncb0_is_max,chd_cnt))
# N5
ok5=0;bad5=[]
for c,cc in COL.items():
    v=cc['pchd']; lst=CHD[v]['bcds']
    hit=[j for j,b in enumerate(lst) if P.dw(b)==cc['ptd']]
    if not hit: bad5.append((hex(c),'nodth')); continue
    # 取 mdisp 相等的那个
    m=[j for j in hit if s32(P.dw(lst[j]+8))==cc['mdisp']]
    if not m: bad5.append((hex(c),'nomdisp')); continue
    ok5+=1
ck('N5a 每个 COL 都能在其 CHD 内找到 (pTD,mdisp) 全等的 BCD',not bad5,(ok5,len(COL)))
# N6 反控
M2bad=0
for v,d in CHD.items():
    for b in d['bcds']:
        ptd=P.dw(b); ncb=P.dw(b+4)
        cands=ALLPTD.get(ptd) or []
        if not cands: continue
        # 取任意一个（第一个）COL 的 CHD
        c0=cands[0]
        if ncb==CHD[COL[c0]['pchd']]['n']-1: M2bad+=1
ck('N6a 反控：用「任意同 pTD 的 COL」代替 own 时 M2 掉下来',M2bad<n_bcd_total,(M2bad,n_bcd_total))
json.dump(dict(col={hex(k):v for k,v in COL.items()},
   chd={hex(k):dict(sig=d['sig'],attr=d['attr'],n=d['n'],arr=hex(d['arr']),bcds=[hex(x) for x in d['bcds']]) for k,d in CHD.items()},
   bcd={hex(k):dict(ptd=hex(v['ptd']),ncb=v['ncb'],mdisp=v['mdisp'],pdisp=v['pdisp'],vdisp=v['vdisp'],attr=v['attr'],chd=hex(v['chd']),idx=v['idx']) for k,v in BCDS.items()},
   models=dict(M1=M1,M2=M2,M3=M3,total=n_bcd_total,chd=chd_cnt,ncb0_n1=ncb0_is_n_minus_1,ncb0_max=ncb0_is_max)),
   open('_r196/m2_ncb.json','w'))
print('--- 断言 %d 条 / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
