#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第二十四刀（终裁 + 撤回）：撤回「占用无 RTTI 数据的占位 TypeDescriptor」这一说法。
自错 S28（本轮的**根因错误**，影响 m2/m4/m5/m6/m7/m8）：我在 m2 的 N2 检查里用
   `P.cstr(td+8, 80)` 读名字，超过 80 字节的**长模板类名**被截断 ⇒ 不以 .?A 开头、
   也不以 @@ 结尾 ⇒ 被误判成「无 RTTI 数据的占位 TypeDescriptor」。
   实测：把上限放到 220 字节后，**2615 个槽位里 0 个**不以 .?A..@@ 结尾。
   ⇒ 我从 m3 到 m7 反复引用的「11 个占位 pTD / 14 个 BCD 位置」**全部作废**，
   它只是 cstr 截断伪影；「占位链不满足 ncb 位置模型」因此也失去解释对象。
   这是本轮最严重的一处自错：它一路传到了 m7 的 V3b/V6b 与 m14 的例外归类。

真终裁（去掉伪影后的干净数据）：
Z1 全部 2615 个 BCD 槽位的 pTD 都有合法的 .?A..@@ 名字，0 例外。
Z2 ncb 语义：ncb[i] == |subtree(i)| - 1，2615/2615 成立（递归建树，m14 T1a）。
Z3 ncb[0] == n-1 == max(ncb)，954/954。
Z4 递归判据的判别力：真 954/954；c-1 只剩 433/1380；c+1 只剩 91/1380。
Z5 相邻元素指针差：递减 1480 / 递增 181 / 恰 -24 973 ⇒「恒 -24」作废，正确说法是
   「同 CHD 内数组元素**多数**递减（1480/1661=89.1%），恰 -24 占 58.6%，故 BCD 在池内共享不连续排布」。
Z6 不同 BCD 地址只有 1002 个 ⇒ 2615 个槽位共享 1002 个结构（平均 2.61 次）。
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
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4])
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
ck('Z0 语料 COL=%d / CHD=%d'%(len(COL),len(CHD)),(len(COL),len(CHD))==(1214,954),(len(COL),len(CHD)))
# Z1
bad=0;lens=[]
for v,d in CHD.items():
    for b in d['bcds']:
        nm=P.cstr(P.dw(b)+8,400)
        lens.append(len(nm) if nm else 0)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): bad+=1
print('   Z1 名字长度：max=%d 中位=%d ; 不以 .?A..@@ 结尾的槽位 = %d'%(max(lens),sorted(lens)[len(lens)//2],bad))
ck('Z1a 全部 2615 槽位的 pTD 名字合法（0 例外）',bad==0,bad)
ck('Z1b 名字长度上限确实超过 80（证明 m2 的 80 字节上限会截断）',max(lens)>80,max(lens))
# Z2
def rec(ncb,n):
    if ncb[0]!=n-1: return False
    par={}
    for i in range(n):
        if ncb[i]<0 or i+ncb[i]>=n: return False
    for i in range(n):
        end=i+ncb[i];k=i+1
        while k<=end:
            par[k]=i;k=k+ncb[k]+1
            if k==0 or k>n: return False
        if k!=end+1: return False
    return len(par)==n-1 and 0 not in par
ok=sum(1 for v,d in CHD.items() if rec([P.dw(b+4) for b in d['bcds']],d['n']))
ck('Z2a ncb 深度优先建树 954/954（c[0]==n-1 且铺满）',ok==954,ok)
# Z3
ok3=sum(1 for v,d in CHD.items() if (lambda nc,n: nc[0]==n-1==max(nc))([P.dw(b+4) for b in d['bcds']],d['n']))
ck('Z3a ncb[0]==n-1==max(ncb) 954/954',ok3==954,ok3)
# Z4
m1ok=m1t=p1ok=p1t=0
for v,d in CHD.items():
    ncb=[P.dw(b+4) for b in d['bcds']];n=d['n']
    for j in range(n):
        if ncb[j]==0: continue
        t=list(ncb);t[j]-=1;m1t+=1
        if rec(t,n): m1ok+=1
        t2=list(ncb);t2[j]+=1;p1t+=1
        if rec(t2,n): p1ok+=1
print('   Z4 反控：c-1 %d/%d ; c+1 %d/%d'%(m1ok,m1t,p1ok,p1t))
ck('Z4a 反控 c-1 通过率 < 50%',m1ok<0.5*m1t,(m1ok,m1t))
ck('Z4b 反控 c+1 通过率 < 50%',p1ok<0.5*p1t,(p1ok,p1t))
# Z5/Z6
dec=inc=eq=ex24=oth=0
for v,d in CHD.items():
    L=d['bcds']
    for j in range(len(L)-1):
        df=L[j+1]-L[j]
        dec+= 1 if df<0 else 0; inc+= 1 if df>0 else 0; eq+= 1 if df==0 else 0
        ex24+= 1 if df==-24 else 0; oth+= 1 if df not in (-24,0) else 0
tot=dec+inc+eq
print('   Z5 相邻对 %d：递减 %d (%.1f%%) / 递增 %d / 相等 %d ; 恰 -24 %d (%.1f%%)'%(tot,dec,100*dec/tot,inc,eq,ex24,100*ex24/tot))
ck('Z5a 递减占多数但非全部（故「恒 -24」作废）',dec<tot and dec>0.8*tot,(dec,tot))
uniq=len({b for v,d in CHD.items() for b in d['bcds']})
ck('Z6a 不同 BCD 地址 1002 / 槽位 2615',uniq==1002,uniq)
print('   Z6 共享倍数 %.2f'%(2615.0/uniq))
json.dump(dict(col=len(COL),chd=len(CHD),bcd_slots=sum(d['n'] for d in CHD.values()),bcd_uniq=uniq,
  name_max=max(lens),name_bad=bad,tree_ok=ok,ncb0_ok=ok3,ctrl=dict(m1=(m1ok,m1t),p1=(p1ok,p1t)),
  stride=dict(tot=tot,dec=dec,inc=inc,eq=eq,ex24=ex24)),
  open('_r196/m24_close.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
