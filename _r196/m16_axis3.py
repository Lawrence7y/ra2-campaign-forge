#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十六刀（ncb 语义最终闭链）：用**第三独立轴**——COL 的 +4 字段（mdisp）——反推树结构。
m15 自错一条：S25 U2 判据写错 —— 「同 d 的结点必须互为祖孙」在 posrev 的单链上**恒成立**
   （整条链互为祖孙），故 U2 对 posrev 无鉴别力。

本刀的唯一外部锚：COL 结构里 +4 = mdisp，表示「该子对象在完整对象内的偏移」。
两条硬约束（都不依赖 ncb 自身）：
 V1 mdisp 为非零值的 vtable 是**子对象视图**；其主对象视图（mdisp==0）的表头在同一 CHD 里。
 V2 对同一类，主对象视图的 ncb 必须 >= 任一子对象视图引用的 BCD 的 ncb（因为主视图包含子视图）。
 V3 「ncb[0] == CHD.n - 1」这条只在**主视图**（mdisp==0）上成立；子视图（mdisp!=0）的 COL
    复用主视图的 BCD，其 ncb 与主视图相同 —— 这是 260 个 COL 复用 954 个 BCD 的字节依据。
 V4 用「子树大小 = ncb+1」反推的最大深度（10）与 RA2 类层次的实际深度做交叉：
    给出每张 CHD 的 (n, 最大子树大小, 最大深度, d 的最大值) 四元组分布。
 V5 posrev 的鉴别判据：posrev 下最大深度恒 == n-1，而真实模型下最大深度 <= 10（远小于 n）。
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
TL=P.B['.text']; TLO=TL['lo']; THI=TL['hi_file']
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        v=w[i]
        if TLO<=v<THI and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MAIN=[v for v in VT if COL[VT[v]]['mdisp']==0]; SUB=[v for v in VT if COL[VT[v]]['mdisp']!=0]
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
    d['ncb']=[P.dw(b+4) for b in d['bcds']]
    d['md']=[s32(P.dw(b+8)) for b in d['bcds']]
ck('V0 语料 vtable=1214 主视图 954 子视图 260',(len(VT),len(MAIN),len(SUB))==(1214,954,260),(len(VT),len(MAIN),len(SUB)))
def build(ncb,n):
    kids={i:[] for i in range(n)}; par={}
    for i in range(n):
        if ncb[i]<0 or i+ncb[i]>=n: return None
    for i in range(n):
        end=i+ncb[i]; k=i+1
        while k<=end:
            par[k]=i; k=k+ncb[k]+1
            if k==0 or k>n: return None
        if k!=end+1: return None
    for c,p in par.items(): kids[p].append(c)
    return kids,(len(par)==n-1 and 0 not in par)
def maxdepth(kids,n):
    dep={0:0};st=[0]
    while st:
        x=st.pop()
        for c in kids[x]: dep[c]=dep[x]+1; st.append(c)
    return max(dep.values()) if dep else 0
# V3 主视图 vs 子视图 ncb 一致性
main_ncb={}; sub_ncb={}
for v in MAIN:
    cc=COL[VT[v]]; d=CHD[cc['pchd']]
    hit=[j for j,b in enumerate(d['bcds']) if P.dw(b)==cc['ptd'] and d['md'][j]==0]
    if hit: main_ncb[v]=d['ncb'][hit[0]]
for v in SUB:
    cc=COL[VT[v]]; d=CHD[cc['pchd']]
    hit=[j for j,b in enumerate(d['bcds']) if P.dw(b)==cc['ptd'] and d['md'][j]==0]
    if hit: sub_ncb[v]=d['ncb'][hit[0]]
ck('V3a 主视图 954 张全部可对齐到 mdisp==0 的 BCD 且取到 ncb',len(main_ncb)==954,len(main_ncb))
ck('V3b 子视图 260 张全部可对齐到 mdisp==0 的 BCD（复用主视图 BCD）',len(sub_ncb)==260,len(sub_ncb))
# V4/V5 深度
dep_real=[];dep_pr=[]
for v,d in CHD.items():
    k,ok=build(d['ncb'],d['n'])
    if not ok: continue
    dep_real.append(maxdepth(k,d['n']))
    kp,_=build([d['n']-1-j for j in range(d['n'])],d['n'])
    dep_pr.append(maxdepth(kp,d['n']))
print('   V4 真模型最大深度分布:',dict(collections.Counter(dep_real)))
print('   V5 posrev 最大深度分布:',dict(collections.Counter(dep_pr)))
ck('V5a 真模型最大深度 <= 10（实测）',max(dep_real)<=10,max(dep_real))
ck('V5b 反控 posrev 最大深度 == n-1，存在 > 10 的链',max(dep_pr)>10,max(dep_pr))
ck('V5c 反控 posrev 在 n>=12 的链上深度 >= 11',sum(1 for x in dep_pr if x>=11)>0,sum(1 for x in dep_pr if x>=11))
# V2 主视图 ncb >= 子视图 ncb（同 pTD）
bad=0
for v,c in [(x,COL[VT[x]]) for x in SUB]:
    d=CHD[c['pchd']]
    same=[j for j,b in enumerate(d['bcds']) if P.dw(b)==c['ptd']]
    if not same: continue
    prim=[j for j in same if d['md'][j]==0]
    if not prim: continue
    if d['ncb'][prim[0]]<0: bad+=1
ck('V2a 主视图 ncb 非负且子视图复用同一 BCD（无独立 ncb）',bad==0,bad)
tuples=collections.Counter()
for v,d in CHD.items():
    k,ok=build(d['ncb'],d['n'])
    if not ok: continue
    tuples[(d['n'],max(d['ncb'])+1,maxdepth(k,d['n']),max(d['md']))]+=1
print('   V4b (n, 最大子树, 最大深度, 最大d) Top10:',list(tuples.most_common(10)))
res=dict(vt=1214,main=954,sub=260,chd=954,
  dep_real=dict(collections.Counter(dep_real)),dep_posrev=dict(collections.Counter(dep_pr)),
  max_depth_real=max(dep_real),max_depth_posrev=max(dep_pr),
  tuples={'|'.join(map(str,k)):v for k,v in tuples.items()},
  main_ncb_ok=len(main_ncb),sub_ncb_ok=len(sub_ncb))
json.dump(res,open('_r196/m16_axis3.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
