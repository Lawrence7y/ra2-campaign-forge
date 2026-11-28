#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m22（§2.12 规则 D：复算审计 #519 的 A1 与 A3 两条订正）。
A1 质疑：「CHD 恰好 40 字节」过强 —— 最小间距 48；+36 在 954 条上都有定义、+40/+44 也有非零。
A3 质疑：「组头 = 组内 mdisp 最大」只有 953/954；稳健定义是「组头 = 组内 vftable 地址最小」954/954。
"""
import sys,struct,collections,json
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
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            VT[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
ck('V0 基数 COL1214/VTI1214/CHD954',(len(COL),len(VT),len(G))==(1214,1214,954),(len(COL),len(VT),len(G)))

print('=== M1 复算 A1：CHD 到底多长 ===')
gaps=[CHD[i+1]-CHD[i] for i in range(len(CHD)-1)]
ck('M1a 相邻 CHD 最小间距 == 48（不是 40）',min(gaps)==48,min(gaps))
ck('M1b 间距==40 的条数 0',gaps.count(40)==0,gaps.count(40))
ck('M1c 间距分布 top6',True,collections.Counter(gaps).most_common(6))
# +36 是否有定义
nz36=sum(1 for a in CHD if P.dw(a+36))
ck('M1d +36 非零的条数 == 205（审计值）',nz36==205,nz36)
ck('M1e +36 全 954 条都有值（含 0）',all(P.dw(a+36) is not None for a in CHD),None)
# +36 目标的结构
t36=set(P.dw(a+36) for a in CHD if P.dw(a+36))
ck('M1f +36 目标去重数',True,len(t36))
seg=collections.Counter(P.where(t) for t in t36)
ck('M1g +36 目标全在 .rdata',seg.get('.rdata',0)==len(t36),dict(seg))
# +36 目标的 12 字节形态 [pTD,0,0,-1]
shape=0
for t in t36:
    d=[P.dw(t+4*k) for k in range(4)]
    if P.where(d[0]) in ('.data','.rdata') and d[1]==0 and d[2]==0 and s32(d[3])==-1: shape+=1
ck('M1h +36 目标形态 [pTD,0,0,-1] 12 字节（审计描述）',shape==len(t36),(shape,len(t36)))
# 至少一个样例打出来
for t in sorted(t36)[:3]:
    print('      +36 目标 0x%x: %s'%(t,[hex(P.dw(t+4*k)) for k in range(4)]))
ck('M1i +40 有值（等于某类 pTD）的条数 == 610（审计值）',
   sum(1 for a in CHD if P.dw(a+40) in set(P.dw(x+28) for x in CHD))==610,
   sum(1 for a in CHD if P.dw(a+40) in set(P.dw(x+28) for x in CHD)))
ck('M1j +44 非零的条数 == 490（审计值）',sum(1 for a in CHD if P.dw(a+44))==490,sum(1 for a in CHD if P.dw(a+44)))
# 关键：a+40 是否可能是下一条 CHD 的起点？最小间距 48 说明不可能是 40
ck('M1k 最小间距 48 > 40 ⇒ a+40..a+47 存在，40 字节不是完整记录',
   min(gaps)>=48 and (min(gaps)-40)>=8,(min(gaps),min(gaps)-40))
ck('M1l a+40 处是 CHD 起点的条数（应为 0，因最小间距 48）',
   sum(1 for a in CHD if a+40 in set(CHD))==0,sum(1 for a in CHD if a+40 in set(CHD)))

print('=== M2 复算 A3：组头定位判据 ===')
def in_text(x): return x is not None and P.B['.text']['lo']<=x<P.B['.text']['hi_file']
def parse(vt,maxk=4000):
    hn=COL[VT[vt]]['name']; cur=VT[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn: views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
HEADS=[]; skip=set(); VIE={}
for vt in sorted(VT):
    if vt in skip: continue
    views,seps=parse(vt); HEADS.append(VT[vt]); skip.add(vt); VIE[VT[vt]]=views
    for p in seps:
        if p+4 in VT: skip.add(p+4)
vt_of={c:k for k,c in VT.items()}
ck('M2a 组头 954 / 视图 1214',(len(HEADS),sum(len(v) for v in VIE.values()))==(954,1214),None)
d_mdmax=sum(1 for h in HEADS if COL[h]['mdisp']==max(COL[x]['mdisp'] for x in VIE[h]))
d_vtmin=sum(1 for h in HEADS if vt_of[h]==min(vt_of[x] for x in VIE[h]))
d_colmin=sum(1 for h in HEADS if h==min(VIE[h]))
ck('M2b 组头 == 组内 mdisp 最大：953/954（审计值）',d_mdmax==953,d_mdmax)
ck('M2c 组头 == 组内 vftable 地址最小：954/954（审计的稳健定义）',d_vtmin==954,d_vtmin)
ck('M2d 组头 == 组内 COL 地址最小：953/954（唯一例外 TerrainClass）',d_colmin==953,d_colmin)
bad=[h for h in HEADS if COL[h]['mdisp']!=max(COL[x]['mdisp'] for x in VIE[h])]
ck('M2e mdisp-max 与 vt-min 两种定义只在同 1 个类上分歧',len(bad)==1 and all(h==bad[0] for h in bad),
   [(hex(h),COL[h]['name']) for h in bad])
for h in bad:
    print('      分歧类 %s 组头 0x%x mdisp=%d；组内: %s'%(COL[h]['name'],h,COL[h]['mdisp'],
          [(hex(c),COL[c]['mdisp'],hex(vt_of[c])) for c in sorted(VIE[h],key=lambda x:vt_of[x])]))
ck('M2f TerrainClass 是唯一「vt 最小但 mdisp 非最大」的类',COL[bad[0]]['name']=='.?AVTerrainClass@@',COL[bad[0]]['name'])
# 决定性：vt 序与 COL 地址序在这一个类上不同
h=bad[0]
ck('M2g 该类的 vt 序 != COL 地址序（唯一一处两序不同）',
   sorted(VIE[h],key=lambda x:vt_of[x])!=sorted(VIE[h]),None)
# 全局：932 组两序相同？
same=sum(1 for h2 in HEADS if sorted(VIE[h2],key=lambda x:vt_of[x])==sorted(VIE[h2]))
ck('M2h 两序相同的组数 == 953（仅 1 组不同）',same==953,same)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,min_gap=min(gaps),nz36=nz36,
               mdmax=d_mdmax,vtmin=d_vtmin,colmin=d_colmin,same_order=same,
               t36=len(t36),plus40=sum(1 for a in CHD if P.dw(a+40) in set(P.dw(x+28) for x in CHD)),
               plus44=sum(1 for a in CHD if P.dw(a+44))),
          open('_r205/m22_audit_a1a3.json','w'),indent=1)
