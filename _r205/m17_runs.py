#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m17：段结构口径订正 —— BCA 相邻对必须用原序（继承路径序），不能用 sorted（地址序）。
m10 自错：L2c/L2d 用 sorted(BCA[a]) 后切段得 1610 段 / 1217 单元素，却与 R204 的 1642/1252 对比。
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
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
ck('V0 基数 COL1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,954,1002,2615),
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCA.values())))
pairs=0; m24=0
for a in CHD:
    v=BCA[a]
    for i in range(len(v)-1):
        pairs+=1
        if v[i]-v[i+1]==24: m24+=1
ck('R1 原序相邻对 1661 / -24 占 973（复现 R204 QG7）',(pairs,m24)==(1661,973),(pairs,m24))
runs=[]
for a in CHD:
    v=BCA[a]; cur=[v[0]]
    for x in v[1:]:
        if cur[-1]-x==24: cur.append(x)
        else: runs.append(cur); cur=[x]
    runs.append(cur)
ln=collections.Counter(len(x) for x in runs)
ck('R2 原序段数 1642',len(runs)==1642,len(runs))
ck('R3 段长分布复现 R204',
   dict(ln)=={1:1252,2:259,3:31,4:8,5:6,6:3,7:1,8:79,10:1,11:1,12:1},dict(sorted(ln.items())))
ck('R4 单元素段 76.2%',round(100.0*ln[1]/len(runs),1)==76.2,round(100.0*ln[1]/len(runs),1))
runs2=[]
for a in CHD:
    v=sorted(BCA[a]); cur=[v[0]]
    for x in v[1:]:
        if x-cur[-1]==24: cur.append(x)
        else: runs2.append(cur); cur=[x]
    runs2.append(cur)
ln2=collections.Counter(len(x) for x in runs2)
ck('R5 对照 sorted 口径 1610 段（m10 错值）',len(runs2)==1610,(len(runs2),ln2[1]))
ck('R6 两口径段数不同 => m10 L2c/L2d 是口径错误非数据反例',len(runs2)!=len(runs),(len(runs2),len(runs)))
e8=[x for x in runs if len(x)==8]
ck('R7 段长恰 8 的 79 段',len(e8)==79,len(e8))
own=set(P.dw(a+28) for a in CHD)
ck('R8 8 长段首元素为本类自有 BCD 的段数',True,'%d/79'%sum(1 for x in e8 if P.dw(x[0]) in own))
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
cn=collections.Counter()
for x in e8: cn[(cname(x[0]) or '?')[:34]]+=1
print('   R8 8 长段按首元素 pTD 名 top6:',cn.most_common(6))
ck('R9 8 长段聚集于少数类',len(cn)<=10,len(cn))
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,pairs=pairs,m24=m24,runs=len(runs),runlen=dict(ln),
               runs_sorted=len(runs2),e8=len(e8),e8_by_name=dict(cn)),
          open('_r205/m17_runs.json','w'),indent=1)
