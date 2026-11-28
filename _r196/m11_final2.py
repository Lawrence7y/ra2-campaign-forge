#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十一刀（ncb 语义最终裁定）：把所有「疑似成立」的模型放在同一张鉴别力表上。
m9/m10 自错四条（全部因为判据缺鉴别力，不进入结论）：
  S16 X6a 用「c-1 扰动」当反控；实测 c-1 后 DFS 仍能消费完 ⇒ 该扰动无鉴别力。
  S17 X2a 「DFS 消费完 954/954」不是充分证据：**全 0 模型同样 954/954**（线性遍历恒消费完）。
  S18 Y3a 「c+1 扰动」同样 1661/2615 通过，无鉴别力。
  S19 Y1d 的 vtable 判据漏了「v 必须在 .text 内」，得 1218 张（应为 1214）。

本刀用**四条互相独立的必要约束**同时卡，任何模型必须全过：
 K1 单根：ncb[0] == n-1（该链是一棵以 [0] 为根的树）
 K2 铺满：每个结点的直接子结点区间恰好铺满其子树，且每个子结点自身合法
 K3 求和：ncb[i] == Σ(ncb[k]+1)，k 取 i 的直接子结点（子树大小 = 1 + 各子树大小）
 K4 单调：沿数组 ncb 单调不增，且每进入一个下一层恰好减 1
再对候选模型（全 0 / 全 n-1 / 按 mdisp==0 计数 / 子树大小）逐个判 PASS/FAIL。
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
ck('K0 语料 CHD=954 / BCD 元素 2615',(len(CHD),sum(d['n'] for d in CHD.values()))==(954,2615),(len(CHD),sum(d['n'] for d in CHD.values())))

def check(ncb,n):
    """返回 (K1,K2,K3,K4)。不递归。"""
    if ncb[0]!=n-1: return (False,False,False,False)
    k2=k3=True; i=0
    while i<n:
        end=i+ncb[i]
        if end>=n: return (True,False,False,False)
        # 直接子结点
        kids=[]; k=i+1
        while k<=end:
            if k+ncb[k]>end: k2=False; break
            kids.append(k); k=k+ncb[k]+1
        if k!=end+1: k2=False
        if ncb[i]!=sum(ncb[x]+1 for x in kids): k3=False
        i=end+1
    if i!=n: k2=False
    k4=all(ncb[j]>=ncb[j+1] for j in range(n-1))
    return (True,k2,k3,k4)

models={
 'real'   : lambda d: d['ncb'],
 'all0'   : lambda d: [0]*d['n'],
 'allN1'  : lambda d: [d['n']-1]*d['n'],
 'mdcount': lambda d: [(d['md'].count(0)-1)-max(0,d['md'][:j+1].count(0)-1) if d['md'][j]==0 else 0 for j in range(d['n'])],
 'posrev' : lambda d: [d['n']-1-j for j in range(d['n'])],
}
tbl={}
for name,f in models.items():
    c1=c2=c3=c4=0
    for v,d in CHD.items():
        a,b,c,e=check(f(d),d['n'])
        c1+=a;c2+=b;c3+=c;c4+=e
    tbl[name]=dict(K1=c1,K2=c2,K3=c3,K4=c4,all=sum(1 for v,d in CHD.items() if all(check(f(d),d['n']))))
    print('   模型 %-8s K1=%d K2=%d K3=%d K4=%d  全过=%d / 954'%(name,c1,c2,c3,c4,tbl[name]['all']))
ck('K1 真实 ncb 通过 K1（单根）954/954',tbl['real']['K1']==954,tbl['real']['K1'])
ck('K2 真实 ncb 通过 K2（铺满）954/954',tbl['real']['K2']==954,tbl['real']['K2'])
ck('K3 真实 ncb 通过 K3（求和）954/954',tbl['real']['K3']==954,tbl['real']['K3'])
ck('K4 真实 ncb 通过 K4（单调不增）954/954',tbl['real']['K4']==954,tbl['real']['K4'])
ck('K5 真实 ncb 四条全过 954/954',tbl['real']['all']==954,tbl['real']['all'])
ck('K6 反控 all0 被 K1 否掉（n>=2 的链全 FAIL）',tbl['all0']['K1']<954,tbl['all0']['K1'])
ck('K7 反控 allN1 被 K2/K3 否掉',tbl['allN1']['all']<954,tbl['allN1']['all'])
ck('K8 反控 mdcount 被否掉',tbl['mdcount']['all']<954,tbl['mdcount']['all'])
ck('K9 反控 posrev(位置逆序) 也被 K2 否掉',tbl['posrev']['all']<954,tbl['posrev']['all'])
# 子树大小分布
sizes=collections.Counter()
for v,d in CHD.items():
    for c in d['ncb']: sizes[c+1]+=1
print('   子树大小（=ncb+1）分布 Top12:',dict(sorted(sizes.items())[:12]))
print('   最大子树大小 =',max(sizes))
res=dict(models=tbl,chd=954,bcd=2615,subtree_sizes=dict(sizes),max_sub=max(sizes),
  kdist=dict(collections.Counter(sum(1 for x in d['md'] if x==0) for v,d in CHD.items())))
json.dump(res,open('_r196/m11_final2.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
