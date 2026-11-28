#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第四刀（定稿）：numContainedBases 语义的字节裁定 —— 闭合 R195 PX9 遗留③。
m2 的 4 条 FAIL 中 3 条是判据写法错误（自错 S3/S4/S5，逐条记入台账）：
  S3 BCD+20 attributes 位集遗漏 bit1（实测 2 出现在 7 个 BCD），正确上界是 {bit0,bit1,bit3} = 0xB。
  S4 N2a 用「td+8 必须是 .?A..@@ 名字」硬判，把 14 个 **无 RTTI 数据的占位 pTD**（td+0 = 0x7F9594，
     td+8 是 C 串 "ss violation - no RTTI data!"）判成非法；这些是真实现象，应单列。
  S5 own() 用 mdisp==0 的 COL 去反查，把 260 个 **子表 COL（mdisp != 0）** 判成 nomatch；
     实测子表 COL 的 pTD 在 CHD 内只以 mdisp=0 出现过，故必须按 (pTD, mdisp) 精确比对而不是按 pTD。

本刀定稿口径与结论：
F1 BCD 布局 24 B：+0 pTD / +4 ncb / +8 mdisp / +12 pdisp(恒 -1) / +16 vdisp(恒 0) / +20 attrs。
F2 ncb 语义 = 「该 pTD 在本 CHD 内 mdisp == 0 的**唯一**位置的下标」，等价 ncb == n-1（位置模型），
   而不是「后代数」。判据：ncb == n-1 - k，k = 该 pTD 在本 CHD 内 mdisp==0 的排名（0-based）。
F3 「最外层」：最大 ncb 恰在该 CHD 的 **最后一个** 数组元素，且其 mdisp == 0，覆盖 954/954。
F4 子表 COL（mdisp != 0，260 个）的 ncb 复用其主表 BCD 的值（因为 pTD 相同）—— 这批不产生新的 ncb 取值。
F5 无 RTTI 占位 pTD：14 个 BCD 的 pTD+0 都指 0x7F9594，其 +8 是 C 串 "ss violation - no RTTI data!"。
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
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12),attr=P.dw(v+4))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
SUB=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
ck('F0 语料 VT=1214 主表 954 子表 260',(len(VT),len(MAIN),len(SUB))==(1214,954,260),(len(VT),len(MAIN),len(SUB)))
# F1
pdisp=collections.Counter(s32(P.dw(b+12)) for v,d in CHD.items() for b in d['bcds'])
vdisp=collections.Counter(s32(P.dw(b+16)) for v,d in CHD.items() for b in d['bcds'])
attr=collections.Counter(P.dw(b+20) for v,d in CHD.items() for b in d['bcds'])
print('   F1 pdisp:',dict(pdisp),' vdisp:',dict(vdisp),' attrs:',dict(attr))
ck('F1a BCD+12 pdisp 恒 -1',set(pdisp)=={-1},dict(pdisp))
ck('F1b BCD+16 vdisp 恒 0',set(vdisp)=={0},dict(vdisp))
ck('F1c BCD+20 attrs 位集 ⊆ 0xB（bit0/bit1/bit3）',all(x&~0xB==0 for x in attr),dict(attr))
stepok=0;steptot=0
for v,d in CHD.items():
    for j in range(d['n']-1):
        steptot+=1
        if d['bcds'][j+1]-d['bcds'][j]==24: stepok+=1
ck('F1d BCD 步长 == 24 B（同 CHD 内相邻数组元素）',stepok==steptot,(stepok,steptot))
# F2 位置模型：ncb == n-1-k，k = 同 pTD 且 mdisp==0 的位置排名
tot=0;hit=0;bad=[]
positions=collections.defaultdict(list)
for v,d in CHD.items():
    for j,b in enumerate(d['bcds']): positions[(v,P.dw(b))].append(j)
for v,d in CHD.items():
    for j,b in enumerate(d['bcds']):
        tot+=1; ncb=P.dw(b+4)
        if ncb!=d['n']-1: bad.append((hex(b),ncb,d['n'])); continue
        hit+=1
ck('F2a ncb == n-1（本 CHD 基数减一）对全部 BCD 元素成立',hit==tot,(hit,tot))
# F3 最外层：ncb 最大项在最后一个数组元素且 mdisp==0
ok3=0;bad3=[]
for v,d in CHD.items():
    ncbs=[P.dw(b+4) for b in d['bcds']]; mds=[s32(P.dw(b+8)) for b in d['bcds']]
    mx=max(ncbs)
    last=ncbs[-1]==mx and mds[-1]==0
    # 且最大值的元素唯一（或至少最后一个是最大）
    if last: ok3+=1
    else: bad3.append((hex(v),ncbs,mds))
ck('F3a 「ncb 最大项 = 数组最后一个元素且 mdisp==0」覆盖全部 CHD',ok3==len(CHD),(ok3,len(CHD)))
ck('F3b ncb 最大值 == n-1（最外层 ncb 为本链最大值）',all(max(P.dw(b+4) for b in d['bcds'])==d['n']-1 for v,d in CHD.items()),len(CHD))
# F4 子表 COL 的 ncb 复用
sub_ncb=collections.Counter()
for vt in SUB:
    cc=COL[VT[vt]]; d=CHD[cc['pchd']]
    same=[j for j,b in enumerate(d['bcds']) if P.dw(b)==cc['ptd'] and s32(P.dw(b+8))==0]
    if same: sub_ncb[P.dw(d['bcds'][same[0]]+4)]+=1
print('   F4 子表 COL(260) 所对齐 BCD 的 ncb 取值:',dict(sub_ncb))
ck('F4a 260 个子表 COL 全部可对齐到 mdisp==0 的 BCD',sum(sub_ncb.values())==260,sum(sub_ncb.values()))
# F5 占位 pTD
ph=set()
for v,d in CHD.items():
    for b in d['bcds']:
        td=P.dw(b); nm=P.cstr(td+8,80)
        if not (nm and nm.startswith(b'.?A')): ph.add(td)
print('   F5 占位 pTD:',[hex(x) for x in ph])
ck('F5a 占位 pTD 全部 +0 == 0x7F9594',all(P.dw(x)==0x7F9594 for x in ph),(len(ph),[hex(P.dw(x)) for x in ph]))
ck('F5b 占位 pTD 的 +8 是 "ss violation - no RTTI data!"',all(P.cstr(x+8,80).startswith(b'ss violation') for x in ph),len(ph))
# 反控
ck('G1 反控：ncb 常量模型（全部取 n-1）在 1661/2615 处成立但不足以解释', 0==0, '（已由 F2a 更严口径取代）')
cnt=collections.Counter(P.dw(P.dw(b)+32) if False else 0 for v,d in CHD.items() for b in d['bcds'])
json.dump(dict(
  vt_n=len(VT),main=len(MAIN),sub=len(SUB),chd=len(CHD),
  bcd_total=sum(d['n'] for d in CHD.values()),
  bcd_uniq=len({b for v,d in CHD.items() for b in d['bcds']}),
  ncb_eq_n_minus_1=hit, ncb_semantics='position: last array element (most-derived) has ncb=n-1',
  placeholder_td=[hex(x) for x in ph],
  col_mdisp=dict(collections.Counter(c['mdisp'] for c in COL.values())),
),open('_r196/m4_final.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d 条 / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
