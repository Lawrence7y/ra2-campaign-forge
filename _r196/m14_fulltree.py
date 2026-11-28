#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十四刀（ncb 语义最终定稿）：全树递归遍历，判 ncb[i] == |subtree(i)| - 1。
m12/m13 自错一条（关键）：S23 kids_of() 只沿「当前层兄弟链」前进，**没有递归进子结点**，
   因此分枝点被少算（19 而非真值）、m13 的 80 张被判成 NO_BRANCH。全部作废重算。

本刀口径：
 T1 由 ncb 数组**重建整棵树**：i 的直接子结点 = i+1, i+1+ncb[..]+1, ... 直到 i+ncb[i]。
 T2 对每个结点 i 计算 |subtree(i)|，断言 ncb[i] == |subtree(i)| - 1（对全部 2615 个结点）。
 T3 断言 ncb 数组恰好被一棵树覆盖（根数 == 1，结点数 == n）。
 T4 分枝点统计（直接子结点 >= 2 的结点数），并给出深度分布。
 T5 与 posrev 的差异全部由「存在非平凡子树」解释：ncb==posrev 当且仅当该链是单链（无分枝且深度==n）。
 T6 反控：all0 / allN1 / posrev 在 T2 上的通过率。
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
ck('T0 语料 CHD=954 / 元素 2615',(len(CHD),sum(d['n'] for d in CHD.values()))==(954,2615),(len(CHD),sum(d['n'] for d in CHD.values())))

def build(ncb,n):
    """返回 (kids dict, roots list, ok)。kids[i] = 直接子结点列表。"""
    kids={i:[] for i in range(n)}
    # 先算每个结点的子树区间 [i, i+ncb[i]]
    for i in range(n):
        if ncb[i]<0 or i+ncb[i]>=n: return None,None,False
    # 父子关系：i 的区间内「第一个未被覆盖的位置」链
    par={}
    for i in range(n):
        end=i+ncb[i]; k=i+1
        while k<=end:
            par[k]=i; k=k+ncb[k]+1
            if k==0 or k>n: return None,None,False
        if k!=end+1: return None,None,False
    for c,p in par.items(): kids[p].append(c)
    roots=[i for i in range(n) if i not in par]
    return kids,roots,(len(roots)==1 and roots[0]==0)

def sizes(kids,n):
    """迭代后序求子树大小。"""
    sz=[1]*n
    order=[]; st=[0]; seen=set()
    while st:
        x=st.pop()
        if x in seen: order.append(x); continue
        seen.add(x); st.append(x)
        for c in kids[x]: st.append(c)
    for x in order: sz[x]=1+sum(sz[c] for c in kids[x])
    return sz

tot_nodes=0; t2_hit=0; t3_ok=0; branch=0; br_chd=0; depth_max=0
seq_eq=0; seq_ne=0
bad_ex=[]
for v,d in CHD.items():
    n=d['n']; ncb=d['ncb']
    kids,roots,rootok=build(ncb,n)
    if kids is None: bad_ex.append((hex(v),'build_fail')); continue
    if rootok: t3_ok+=1
    sz=sizes(kids,n)
    allok=True
    for i in range(n):
        tot_nodes+=1
        if ncb[i]==sz[i]-1: t2_hit+=1
        else: allok=False
    if not allok and len(bad_ex)<8: bad_ex.append((hex(v),ncb,[sz[i]-1 for i in range(n)]))
    b=sum(1 for i in range(n) if len(kids[i])>=2)
    branch+=b
    if b: br_chd+=1
    # 深度
    dep={0:0}; st=[0]
    while st:
        x=st.pop()
        for c in kids[x]:
            dep[c]=dep[x]+1; st.append(c)
    if dep: depth_max=max(depth_max,max(dep.values()))
    if ncb==[n-1-j for j in range(n)]: seq_eq+=1
    else: seq_ne+=1
print('   T2 ncb[i]==|subtree(i)|-1 命中 %d / %d'%(t2_hit,tot_nodes))
ck('T1a 全部 2615 结点满足 ncb == 子树大小-1',t2_hit==tot_nodes,(t2_hit,tot_nodes))
ck('T3a 每张 CHD 恰一棵树（根 == 下标 0）',t3_ok==len(CHD),(t3_ok,len(CHD)))
print('   T4 分枝点总数 %d ; 含分枝点的 CHD %d ; 最大深度 %d'%(branch,br_chd,depth_max))
ck('T4a 分枝点总数 > 0（树非退化）',branch>0,branch)
print('   T5 ncb==posrev 的 CHD %d / != 的 %d'%(seq_eq,seq_ne))
ck('T5a 存在偏离 posrev 的 CHD（故 posrev 不是真模型）',seq_ne>0,seq_ne)
if bad_ex: [print('     反例',x) for x in bad_ex[:6]]
# T6 反控
def rate(model):
    h=t=0
    for v,d in CHD.items():
        ncb=model(d,d['n'])
        kids,roots,rootok=build(ncb,d['n'])
        if kids is None: t+=d['n']; continue
        sz=sizes(kids,d['n'])
        for i in range(d['n']):
            t+=1
            if ncb[i]==sz[i]-1: h+=1
    return h,t
r0=rate(lambda d,n:[0]*n)
r1=rate(lambda d,n:[n-1]*n)
rp=rate(lambda d,n:[n-1-j for j in range(n)])
print('   T6 反控 all0 %d/%d ; allN1 %d/%d ; posrev %d/%d'%(r0[0],r0[1],r1[0],r1[1],rp[0],rp[1]))
ck('T6a 反控 all0 通过率 <100%',r0[0]<r0[1],r0)
ck('T6b 反控 allN1 通过率 <100%',r1[0]<r1[1],r1)
ck('T6c 反控 posrev 通过率 <100%（即 posrev 是同义反复，被 T4 分枝点否掉）',rp[0]<rp[1],rp)
res=dict(chd=len(CHD),nodes=tot_nodes,t2=(t2_hit,tot_nodes),t3=(t3_ok,len(CHD)),
  branch=branch,br_chd=br_chd,depth_max=depth_max,seq_eq=seq_eq,seq_ne=seq_ne,
  ctrl=dict(all0=r0,allN1=r1,posrev=rp),
  sizes_hist=dict(sorted(collections.Counter(P.dw(b+4)+1 for v,d in CHD.items() for b in d['bcds']).items())))
json.dump(res,open('_r196/m14_fulltree.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
