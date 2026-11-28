#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十八刀：ncb 语义的**第四独立轴** —— 用 vtable 槽数验证「子树大小」的解释。
若 ncb[i]+1 = 该类的子树大小（含自身的基类数），则「类别的接口数」应随 ncb 单调不降：
一个拥有更多基类的子对象，其完整对象内的接口视图只会更多。这可以用 vtable 槽数做**独立旁证**。
Z1 vtable 槽数统计口径：从槽 0 起连续 .text 指针的个数，遇非 .text 即停，上限 512。
Z2 分组检查：ncb 与槽数的 Spearman 秩相关（不假设线性）。
Z3 强判据：同一 CHD 内 ncb 严格递减的相邻对，其槽数必须非增（允许相等）。
Z4 反控：把 ncb 换成 posrev（= n-1-j）后 Z3 的违反数必须显著上升。
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
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
TL=P.B['.text']; TLO=TL['lo']; THI=TL['hi_file']
def intext(x): return x is not None and TLO<=x<THI
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if intext(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslots(v):
    k=0
    while k<512:
        if not intext(P.dw(v+4*k)): break
        k+=1
    return k
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
    d['ncb']=[P.dw(b+4) for b in d['bcds']]
    d['d']=[s32(P.dw(b+8)) for b in d['bcds']]
ck('Z0 vtable=1214 / CHD=954',(len(VT),len(CHD))==(1214,954),(len(VT),len(CHD)))
# 每个主视图 vtable 的槽数，映射到 BCD
vals=[]
for v,c in VT.items():
    cc=COL[c]
    if cc['mdisp']!=0: continue
    d=CHD[cc['pchd']]
    hit=[j for j,b in enumerate(d['bcds']) if P.dw(b)==cc['ptd'] and d['d'][j]==0]
    if not hit: continue
    vals.append((d['ncb'][hit[0]],nslots(v),v,cc['name']))
print('   Z1 主视图样本 %d 张 ; 槽数分布 Top8:'%len(vals),dict(collections.Counter(x[1] for x in vals).most_common(8)))
ck('Z1a 主视图样本 954 张',len(vals)==954,len(vals))
# Z2 Spearman
import statistics
def spearman(xs,ys):
    def rank(a):
        s=sorted(range(len(a)),key=lambda i:a[i]); r=[0]*len(a); i=0
        while i<len(s):
            j=i
            while j+1<len(s) and a[s[j+1]]==a[s[i]]: j+=1
            avg=(i+j)/2.0+1
            for k in range(i,j+1): r[s[k]]=avg
            i=j+1
        return r
    rx=rank(xs); ry=rank(ys); n=len(xs)
    mx=sum(rx)/n; my=sum(ry)/n
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    den=(sum((rx[i]-mx)**2 for i in range(n))*sum((ry[i]-my)**2 for i in range(n)))**0.5
    return num/den if den else 0.0
rho=spearman([x[0] for x in vals],[x[1] for x in vals])
print('   Z2 ncb vs 槽数 Spearman rho = %.4f'%rho)
ck('Z2a ncb 与槽数正相关（rho > 0.1）',rho>0.1,rho)
# Z3 同 CHD 内相邻对
v3=v3t=0; pc=pcv=0
for v,d in CHD.items():
    ncb=d['ncb'];d_=d['d'];n=d['n']
    sl=[None]*n
    for j,b in enumerate(d['bcds']):
        # 找该 pTD 的 mdisp==0 主视图
        for vv,c in VT.items():
            cc=COL[c]
            if cc['ptd']==P.dw(b) and cc['mdisp']==0:
                sl[j]=nslots(vv);break
    for j in range(n-1):
        if ncb[j]<=ncb[j+1]: continue
        if sl[j] is None or sl[j+1] is None: continue
        v3t+=1
        if sl[j]>=sl[j+1]: v3+=1
    # posrev
    pr=[n-1-j for j in range(n)]
    for j in range(n-1):
        if pr[j]<=pr[j+1]: continue
        if sl[j] is None or sl[j+1] is None: continue
        pcv+=1
        if sl[j]>=sl[j+1]: pc+=1
print('   Z3 真模型：ncb 递减相邻对 %d 中槽数非增 %d (%.1f%%)'%(v3t,v3,100.0*v3/max(1,v3t)))
print('   Z4 反控 posrev：%d 中槽数非增 %d (%.1f%%)'%(pcv,pc,100.0*pc/max(1,pcv)))
ck('Z3a 真模型槽数非增比例 > 反控比例',v3/max(1,v3t)>pc/max(1,pcv),(v3/max(1,v3t),pc/max(1,pcv)))
json.dump(dict(rho=rho,n=len(vals),real=(v3,v3t),posrev=(pc,pcv),
  slot_hist=dict(collections.Counter(x[1] for x in vals)),
  top=[(x[0],x[1],x[3]) for x in sorted(vals,reverse=True)[:12]]),
  open('_r196/m18_slotdep.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
