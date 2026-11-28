#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m19（§2.12 规则 D：复算审计员 #519 的 A6 独立发现）：
「组内 mdisp 严格递减」在**哪种序**下成立 —— vt 序 3 例外，COL 地址序 0 例外。
若成立，则 R205 正文「3 个非递减反例」应改为「vt 序 3 例外，地址序 954/954 严格递减」。
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
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pchd=w[i+4],name=nm.decode('latin1'))
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
ck('V0 基数 COL1214/VTI1214/CHD954',(len(COL),len(VTI),len(G))==(1214,1214,954),(len(COL),len(VTI),len(G)))
def in_text(x): return x is not None and P.B['.text']['lo']<=x<P.B['.text']['hi_file']
def parse(vt,maxk=4000):
    hn=COL[VTI[vt]]['name']; cur=VTI[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn: views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
HEADS=[]; skip=set(); VIE={}
for vt in sorted(VTI):
    if vt in skip: continue
    views,seps=parse(vt); HEADS.append(VTI[vt]); skip.add(vt); VIE[VTI[vt]]=views
    for p in seps:
        if p+4 in VTI: skip.add(p+4)
ck('V1 组头 954 / 视图 1214（复现）',(len(HEADS),sum(len(v) for v in VIE.values()))==(954,1214),
   (len(HEADS),sum(len(v) for v in VIE.values())))

# ---------- N1 vt 序（解析顺序） ----------
bad_vt=[]
tot=0
for h in HEADS:
    v=VIE[h]
    for i in range(len(v)-1):
        tot+=1
        if COL[v[i]]['mdisp']<=COL[v[i+1]]['mdisp']: bad_vt.append((hex(h),COL[h]['name'],i,
            [COL[x]['mdisp'] for x in v]))
ck('N1a vt 序：260 个相邻对中 3 个非严格递减（复现 m8/m13）',tot==260 and len(bad_vt)==3,(tot,len(bad_vt)))

# ---------- N2 COL 地址序 ----------
bad_ad=[]
tot2=0
for h in HEADS:
    v=sorted(VIE[h])          # 按 COL 地址升序
    for i in range(len(v)-1):
        tot2+=1
        if COL[v[i]]['mdisp']<=COL[v[i+1]]['mdisp']:
            bad_ad.append((hex(h),COL[h]['name'],i,[COL[x]['mdisp'] for x in v]))
ck('N2a COL 地址序：260 个相邻对中 0 个非严格递减（审计 #519 的独立发现）',
   tot2==260 and len(bad_ad)==0,(tot2,len(bad_ad)))
ck('N2b 地址序下 mdisp 严格递减 954/954',
   all(all(COL[v[i]]['mdisp']>COL[v[i+1]]['mdisp'] for i in range(len(v)-1))
       for v in (sorted(VIE[h]) for h in HEADS)),None)
# 3 个 vt 序反例在地址序下的样子
for h,name,i,seq in bad_vt:
    hh=int(h,16)
    print('   反例 %s：vt序=%s 地址序=%s'%(name[:30],seq,[COL[x]['mdisp'] for x in sorted(VIE[hh])]))

# ---------- N3 地址序下组内首尾 ----------
ck('N3a 地址序首元素恒为 mdisp 最大、末元素恒为 mdisp==0（即 CHD+16）',
   all(COL[sorted(VIE[h])[0]]['mdisp']>0 and COL[sorted(VIE[h])[-1]]['mdisp']==0
       for h in HEADS if len(VIE[h])>1),None)
ck('N3b 单视图类 860 个（首=末=CHD+16）',
   sum(1 for h in HEADS if len(VIE[h])==1)==860,sum(1 for h in HEADS if len(VIE[h])==1))
# 地址序是否恒等于 mdisp 降序（更强）
eq=sum(1 for h in HEADS if [COL[x]['mdisp'] for x in sorted(VIE[h])]==
       sorted([COL[x]['mdisp'] for x in VIE[h]],reverse=True))
ck('N4 COL 地址升序 == mdisp 严格降序 954/954（地址序与 mdisp 序方向相反）',eq==954,eq)
# m19 自错：首版写「地址降序==mdisp降序」方向反了，实测 860（=单视图类数）

# ---------- N5 反控 ----------
# 若打乱地址序（用 vt 序），则不成立 3 处 —— 说明「同向」不是恒真
ck('C1 反控：vt 序下该律有 3 例外（非恒真）',len(bad_vt)==3,len(bad_vt))
# 随机重排一个多视图组，律应破
import random
random.seed(2061)
h=[x for x in HEADS if len(VIE[x])==4][0]
v=list(VIE[h]); random.shuffle(v)
ok=all(COL[v[i]]['mdisp']>COL[v[i+1]]['mdisp'] for i in range(len(v)-1))
ck('C2 反控：随机重排一个 4 视图组后递减律破坏',ok==False,ok)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,tot_pairs=tot,bad_vt=len(bad_vt),bad_ad=len(bad_ad),
               order_eq=eq),open('_r205/m19_addrorder.json','w'),indent=1)
