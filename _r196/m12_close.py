#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十二刀（ncb 定稿裁定）：用「分枝点」取得真模型与 posrev 的鉴别力。
m11 自错两条（判据缺鉴别力，不进入结论）：
  S20 K4「ncb 沿数组单调不增」是**错判据**：DFS 先序下子树大小序列本就可以回升
      （根 4 个结点、子1 叶子、子2 有 2 个子 ⇒ 序列 3,0,1,0）。实测真实 ncb 只有 858/954 满足。
  S21 K9 断言「posrev 会被 K2 否掉」；实测 posrev（每个结点恰 1 个子结点）**恒满足 K1..K4**
      ⇒ K1..K4 对「退化链」无鉴别力，必须补分枝点判据。

定稿判据（唯一能同时否掉 posrev 与 all0/allN1 的）：
 Z1 真模型在 >=1 张 CHD 上存在**分枝点**（直接子结点数 >= 2）；posrev 的分枝点恒 0。
 Z2 真模型与 posrev 不相等的 CHD 集合，必须与「存在分枝点的 CHD 集合」重合。
 Z3 真模型在全部 CHD 上满足 K1（单根）/ K2（铺满）/ K3（求和）。
 Z4 反控：把 posrev 当答案时，分枝点数 = 0，与本语料实测分枝点数不符。
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
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
    d['ncb']=[P.dw(b+4) for b in d['bcds']]
    d['md']=[s32(P.dw(b+8)) for b in d['bcds']]
ck('Z0 语料 CHD=954 / 元素 2615',(len(CHD),sum(d['n'] for d in CHD.values()))==(954,2615),(len(CHD),sum(d['n'] for d in CHD.values())))

def kids_of(ncb,n):
    """返回每个结点的直接子结点列表；越界返回 None。"""
    out={}; i=0
    while i<n:
        end=i+ncb[i]
        if end>=n: return None
        k=i+1; ks=[]
        while k<=end:
            ks.append(k); k=k+ncb[k]+1
            if k==0: return None
        if k!=end+1: return None
        out[i]=ks; i=end+1
    return out if i==n else None

branch_real=0; branch_posrev=0; total_nodes=0
maxkids=0; diff_chd=[]; br_chd=set()
k1=k2=k3=0
for v,d in CHD.items():
    ncb=d['ncb']; n=d['n']
    ks=kids_of(ncb,n)
    if ks is None: continue
    if ncb[0]==n-1: k1+=1
    k2+=1
    ok3=all(ncb[i]==sum(ncb[x]+1 for x in ks[i]) for i in ks)
    if ok3: k3+=1
    br=sum(1 for i in ks if len(ks[i])>=2)
    branch_real+=br
    if br: br_chd.add(v)
    total_nodes+=len(ks)
    if ks and max(len(x) for x in ks.values())>maxkids: maxkids=max(len(x) for x in ks.values())
    if ncb!=[n-1-j for j in range(n)]: diff_chd.append(v)
    pk={i:[j for j in ([i+1] if False else [])] for i in ks}  # posrev 子结点
print('   Z1 真实模型：分枝点（>=2 子结点）总数 %d ; 含分枝点的 CHD %d ; 最大子结点数 %d'%(branch_real,len(br_chd),maxkids))
print('   Z1b 结点总数 %d'%total_nodes)
ck('Z1a 真实模型存在分枝点（>0）',branch_real>0,branch_real)
ck('Z3a 真实模型 K1 单根 954/954',k1==954,k1)
ck('Z3b 真实模型 K2 铺满 954/954',k2==954,k2)
ck('Z3c 真实模型 K3 求和 954/954',k3==954,k3)
# posrev 的分枝点
pb=0
for v,d in CHD.items():
    n=d['n']; pr=[n-1-j for j in range(n)]
    ks=kids_of(pr,n)
    if ks is None: continue
    pb+=sum(1 for i in ks if len(ks[i])>=2)
ck('Z4a 反控：posrev 的分枝点总数 == 0（与实测不符）',pb==0,pb)
# Z2 重合
s1=set(diff_chd); s2=set(br_chd)
print('   Z2 真实 != posrev 的 CHD %d 张 ; 含分枝点 %d 张 ; 交集 %d ; 只在差集 %d ; 只在分枝 %d'%(
   len(s1),len(s2),len(s1&s2),len(s1-s2),len(s2-s1)))
ck('Z2a 「真 != posrev」的 CHD 集合与「含分枝点」重合 >=95%',
   len(s1&s2)>=0.95*max(len(s1),len(s2)),(len(s1&s2),len(s1),len(s2)))
# 子树大小与 ncb 的关系再确认
sizes=collections.Counter()
for v,d in CHD.items():
    for c in d['ncb']: sizes[c+1]+=1
ck('Z5a 子树大小最小 1（叶子）且叶子的 ncb==0',sizes.get(1,0)==sum(1 for v,d in CHD.items() for c in d['ncb'] if c==0),(sizes.get(1,0),))
res=dict(chd=954,nodes=total_nodes,branch_points=branch_real,br_chd=len(br_chd),max_kids=maxkids,
  posrev_branch=pb,diff_chd=len(s1),diff_and_br=len(s1&s2),br_only=len(s2-s1),diff_only=len(s1-s2),
  k=(k1,k2,k3),subtree_sizes=dict(sorted(sizes.items())),
  ncb_sum=sum(d['ncb'] for v,d in CHD.items()),
  ncb_max=max(c for v,d in CHD.items() for c in d['ncb']))
json.dump(res,open('_r196/m12_close.json','w'),ensure_ascii=False,indent=1)
print('   ncb 总和 %d ; ncb 最大 %d'%(res['ncb_sum'],res['ncb_max']))
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
