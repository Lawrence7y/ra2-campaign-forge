#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第六刀：G-clean 组 34 处 (m5 C3a) 例外的定位与成因裁定。
E1 列出 G-clean 且 n>=3 里 ncb != n-1-j 的全部样本（CHD / j / pTD 名 / ncb / 期望值 / mdisp）。
E2 检验成因假设 H1：这些 CHD 内存在「pTD 不同但名字相同」的重复基类（pTD 去重判据漏掉的同名重复）。
E3 检验假设 H2：这些 CHD 内 mdisp 序列不是单调递增（0,4,8,12...）而是跳号 —— 跳号即「该基类在本链里被折叠」。
E4 反控口径修正：只用 n>=3 的 G-clean CHD 才能让「方向反」判据有意义（n<3 时 j 与 n-1-j 重合）。
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
def nmof(b):
    t=P.cstr(P.dw(P.dw(b))+8,120); return t.decode('latin1') if t else '?'
rows=[]
for v,d in CHD.items():
    pt=[P.dw(b) for b in d['bcds']]
    if len(set(pt))!=len(pt): continue
    for j,b in enumerate(d['bcds']):
        if P.dw(b+4)!=d['n']-1-j:
            rows.append((v,j,d['n'],P.dw(b),nmof(b),P.dw(b+4),d['n']-1-j,s32(P.dw(b+8)),
                         [nmof(x) for x in d['bcds']],[s32(P.dw(x+8)) for x in d['bcds']]))
print('=== E1 G-clean 且偏离 ncb==n-1-j 的样本共 %d 条 ==='%len(rows))
for r in rows[:40]:
    print(' CHD %08X j=%d n=%d pTD=%08X %-40s ncb=%d 期望 %d mdisp=%d'%(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7]))
    print('    链名:',[x.replace('.?A','').replace('@@','') for x in r[8]])
    print('    链md:',r[9])
# E2 同名重复
e2=0
for r in rows:
    if len(set(r[8]))!=len(r[8]): e2+=1
print('   E2 其中「链内同名重复」的条数 = %d / %d'%(e2,len(rows)))
# E3 mdisp 单调性
e3=0
for r in rows:
    md=r[9]
    if any(md[i]>=md[i+1] for i in range(len(md)-1)): e3+=1
print('   E3 其中「mdisp 非严格递增」的条数 = %d / %d'%(e3,len(rows)))
# 全语料 mdisp 单调性
mono=nonm=0;nonm_chd=[]
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    if all(md[i]<md[i+1] for i in range(len(md)-1)): mono+=1
    else: nonm+=1; nonm_chd.append((v,md))
print('   E3b 全语料：mdisp 严格递增的 CHD %d / 非递增 %d'%(mono,nonm))
for v,md in nonm_chd[:8]: print('      %08X %s'%(v,md))
ck('E3c mdisp 严格递增覆盖 >=95%% 的 CHD',mono>=0.95*len(CHD),(mono,len(CHD)))
# E4 反控修正（n>=3）
bad=0;tot=0
for v,d in CHD.items():
    pt=[P.dw(b) for b in d['bcds']]
    if len(set(pt))!=len(pt) or d['n']<3: continue
    for j,b in enumerate(d['bcds']):
        tot+=1
        if P.dw(b+4)==j: bad+=1
print('   E4 n>=3 的 G-clean：方向反(ncb==j) 命中 %d / %d = %.1f%%'%(bad,tot,100.0*bad/tot))
ck('E4a 反控在 n>=3 G-clean 上命中率 < 30%%',bad<0.3*tot,(bad,tot))
# G-clean n>=3 下 ncb==n-1-j 命中率
hit=tot2=0
for v,d in CHD.items():
    pt=[P.dw(b) for b in d['bcds']]
    if len(set(pt))!=len(pt) or d['n']<3: continue
    for j,b in enumerate(d['bcds']):
        tot2+=1
        if P.dw(b+4)==d['n']-1-j: hit+=1
print('   E4 G-clean n>=3：ncb==n-1-j 命中 %d / %d = %.2f%%'%(hit,tot2,100.0*hit/tot2))
ck('E4b G-clean n>=3 上 ncb==n-1-j 命中率 >= 97%%',hit>=0.97*tot2,(hit,tot2))
json.dump(dict(resid=len(rows),e2=e2,e3=e3,mono=mono,nonmono=nonm,
  rev=(bad,tot),pos=(hit,tot2),
  samples=[dict(chd=hex(r[0]),j=r[1],n=r[2],ptd=hex(r[3]),name=r[4],ncb=r[5],exp=r[6],mdisp=r[7],
                chain=[x.replace('.?A','').replace('@@','') for x in r[8]],mds=r[9]) for r in rows]),
  open('_r196/m6_resid.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
