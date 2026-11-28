#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十五刀（ncb 特异性最终裁定）：用「与 d 字段的联合约束」取得真正的鉴别力。
m14 自错一条：S24 T6 的反控是同义反复 —— sizes() 由 ncb 自身推出，故任何自洽模型都 100% 通过
   （all0 2615/2615、posrev 2615/2615）。这不是数据问题，是判据设计的循环论证。

真正的外部约束：ncb 树必须与 BCD 的 d 字段（第 +8 字段）一致：
 U1 子树关系蕴含 d 单调：子结点的 d >= 父结点的 d（实测 m9 X7a 2615/2615）。
 U2 d 相同的结点必须是**祖先-后代关系**（同一虚基组），不能是兄弟。
 U3 posrev 的树是全退化单链，其 d 序列必须单调不减；实测 99 张 CHD 的 d 序列有回落
    ⇒ posrev 在这 99 张上必然违反 U2（兄弟 d 相同或祖先违反）。
 U4 all0 的树是「全兄弟」，d 相同的元素必然成为兄弟 ⇒ 违反 U2。
 U5 逐张给出 U2 的违反计数（真模型应 0）。
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
    d['ncb']=[P.dw(P.dw(d['arr']+4*j)+4) for j in range(d['n'])]
    d['md']=[s32(P.dw(P.dw(d['arr']+4*j)+8)) for j in range(d['n'])]
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
ck('U0 CHD=954 / 元素 2615',(len(CHD),sum(d['n'] for d in CHD.values()))==(954,2615),(len(CHD),sum(d['n'] for d in CHD.values())))
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
def judge(ncb,md,n):
    """返回 (U1违反, U2违反, ok)。U2: 同 d 的结点必须互为祖先-后代。"""
    r=build(ncb,n)
    if r is None: return (999,999,False)
    kids,rootok=r
    if not rootok: return (999,999,False)
    # 祖先集
    anc={i:set() for i in range(n)}; st=[(0,set())]
    order=[];q=[0]
    par={}
    for p,ks in kids.items():
        for c in ks: par[c]=p
    for i in range(n):
        x=i
        while x in par:
            x=par[x]; anc[i].add(x)
    u1=0
    for i in range(n):
        for a in anc[i]:
            if md[i]<md[a]: u1+=1
    # U2: 同 d 的非祖孙对
    bymd=collections.defaultdict(list)
    for i in range(n): bymd[md[i]].append(i)
    u2=0
    for v_,lst in bymd.items():
        for x in range(len(lst)):
            for y in range(x+1,len(lst)):
                a,b=lst[x],lst[y]
                if a not in anc[b] and b not in anc[a]: u2+=1
    return (u1,u2,True)
res={}
for name,f in [('real',lambda d:[P.dw(b+4) for b in d['bcds']]),
               ('posrev',lambda d:[d['n']-1-j for j in range(d['n'])]),
               ('all0',lambda d:[0]*d['n']),
               ('allN1',lambda d:[d['n']-1]*d['n'])]:
    ok=0;u1s=u2s=0
    for v,d in CHD.items():
        a,b,c=judge(f(d),d['md'],d['n'])
        if c: ok+=1
        if a==0: u1s+=1
        if b==0 and c: u2s+=1
    res[name]=dict(ok=ok,u1clean=u1s,u2clean=u2s)
    print('   模型 %-7s 可建树 %d/954 ; U1 无违反 %d ; U2 无违反 %d'%(name,ok,u1s,u2s))
ck('U1a 真模型 U1（子 d >= 父 d）无违反 954/954',res['real']['u1clean']==954,res['real']['u1clean'])
ck('U2a 真模型 U2（同 d 必为祖孙）无违反 954/954',res['real']['u2clean']==954,res['real']['u2clean'])
ck('U3a 反控 posrev：U2 有违反（<954 张干净）',res['posrev']['u2clean']<954,res['posrev']['u2clean'])
ck('U4a 反控 all0：U2 有违反',res['all0']['u2clean']<954,res['all0']['u2clean'])
ck('U5a 反控 allN1：无法建树或 U2 违反',res['allN1']['u2clean']<954,res['allN1']['u2clean'])
json.dump(dict(models=res,chd=954),open('_r196/m15_disc.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
