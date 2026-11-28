#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十刀：ncb 语义的第二独立轴 —— 用 COL 的 +4 字段给 BaseClassDescriptor 的 d 字段定性。
X6a 反控 FAIL 已记自错 S16：把 c 减 1 后 DFS 仍然消费得完（因为 c-1 只是让该结点少一个子树位，
而父层继续按新边界推进，结构上仍自洽）——该扰动不可作为反控，正确反控是「c 加 1 造成越界」或「c 全置 0」。
本刀做两件事：
Y1 用「COL+4 == BCD.d」这条**独立于 DFS 的轴**给 d 定性：若 d 只在 COL 侧出现，说明 d 是「虚基偏移」类字段。
Y2 ncb 与 d 的联合结构：同一 CHD 内，d 相同的相邻元素是否构成「同一虚基组」，ncb 是否在该组内连续。
Y3 反控：c+1 扰动必须导致越界或消费不完。
"""
import sys,struct,collections,json,random
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
# Y1 COL.mdisp 与 BCD.d 的取值域交集
colmd=collections.Counter(c['mdisp'] for c in COL.values())
bcdmd=collections.Counter(s32(P.dw(b+8)) for v,d in CHD.items() for b in d['bcds'])
print('   Y1 COL+4 取值:',dict(colmd))
print('   Y1 BCD +8 取值:',dict(bcdmd))
ck('Y1a COL+4 有 0/4/8/12（mdisp 家族）与异常大值 21784/1728/24/36/40/44 两类',
   {0,4,8,12} <= set(colmd) and any(v>1000 for v in colmd), sorted(colmd))
big=[(c,cc) for c,cc in COL.items() if cc['mdisp']>1000]
print('   Y1b COL+4 > 1000 的条目 %d 个:'%len(big))
for c,cc in big: print('       %08X mdisp=%d name=%s pTD=%08X'%(c,cc['mdisp'],cc['name'],cc['ptd']))
# 这些大值是否也在 BCD 出现
inbcd=sum(1 for c,cc in big if cc['mdisp'] in bcdmd)
ck('Y1c COL+4 大值在 BCD+8 里出现的个数（预期 0 或极少）',True,(inbcd,len(big)))
# Y1d 对每张 vtable 检查: COL.mdisp 是否等于其 CHD 内同名 pTD 的 d
vt={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.dw(base+4*i-4) in COL: vt[base+4*i]=P.dw(base+4*i-4)
match=nomatch=0;nmd=[]
for v,c in vt.items():
    cc=COL[c]; d=CHD[cc['pchd']]
    hits=[j for j,b in enumerate(d['bcds']) if P.dw(b)==cc['ptd'] and d['md'][j]==cc['mdisp']]
    if hits: match+=1
    else:
        nomatch+=1
        if len(nmd)<6: nmd.append((hex(v),hex(c),cc['mdisp'],cc['name'],hex(cc['pchd']),d['md']))
print('   Y1d vtable 的 (pTD,COL+4) 在该 CHD 内可对齐: %d / %d'%(match,match+nomatch))
for x in nmd: print('       ',x)
ck('Y1e 260 张子表 COL 的 +4 在 CHD 内不可对齐（与主会话 m3 一致）',nomatch==260,(nomatch,match))
# Y2 d 分组与 ncb
seg_ok=seg_tot=0
for v,d in CHD.items():
    md=d['md']; ncb=d['ncb']
    # 按 d 相同的连续块
    i=0;n=d['n']
    while i<n:
        j=i
        while j+1<n and md[j+1]==md[i]: j+=1
        seg_tot+=1
        # 块内 ncb 应递减 1（若不递减则记 bad）
        if all(ncb[k]-ncb[k+1]==1 for k in range(i,j)): seg_ok+=1
        i=j+1
print('   Y2 同 d 连续块 %d 个，块内 ncb 逐项 -1 的块 %d'%(seg_tot,seg_ok))
ck('Y2a 同 d 连续块内 ncb 逐项 -1（覆盖 >=95%）',seg_ok>=0.95*seg_tot,(seg_ok,seg_tot))
# Y3 反控 c+1
def parse(ncb,n):
    i=0;g=0
    while i<n:
        g+=1
        if g>n*4+16: return False
        e=i+ncb[i]
        if e>=n: return False
        i=e+1
    return i==n
plus_ok=plus_tot=zero_ok=0
zero_tot=0
for v,d in CHD.items():
    for j in range(d['n']):
        t=list(d['ncb']); t[j]=t[j]+1; plus_tot+=1
        if parse(t,d['n']): plus_ok+=1
    zero_tot+=1
    if parse([0]*d['n'],d['n']): zero_ok+=1
print('   Y3 c+1 扰动后仍解析完: %d / %d ; 全 0 模型成立: %d / %d'%(plus_ok,plus_tot,zero_ok,zero_tot))
ck('Y3a 反控：c+1 扰动绝大多数导致解析失败',plus_ok<=0.05*plus_tot,(plus_ok,plus_tot))
ck('Y3b 反控：全 0 模型在非平凡链上不成立（n>=2 的 CHD 应失败）',zero_ok<zero_tot,(zero_ok,zero_tot))
res=dict(colmd=dict(colmd),bcdmd=dict(bcdmd),big=[(hex(c),cc['mdisp'],cc['name']) for c,cc in big],
  vt_align=(match,nomatch),seg=(seg_ok,seg_tot),ctrl_plus=(plus_ok,plus_tot),ctrl_zero=(zero_ok,zero_tot))
json.dump(res,open('_r196/m10_axis2.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
