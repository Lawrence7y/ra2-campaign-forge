#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第四刀：虚表槽位顺序 ↔ 实现地址局部性（vtable 布局是「按基类分段」还是「随机」）。
判据：
 L1 基线 1214/1214/14044。
 L2 对每张表，相邻槽目标落在同一 4KB 页的比例 same_page / (N-1)。
 L3 反控：把每张表的槽序随机打乱 20 次，同页比例均值（若实测远高于打乱均值 => 布局有段结构）。
 L4 对 8 张超长表（>=128 槽）逐张给 same_page 比例 + 同页 run 个数。
 L5 8 张超长表的「同页 run」是否与继承链顺序对应：给出每张表 slot 0..N 的页号序列压缩表示。
 L6 反控 2：把页粒度从 4KB 改成 64KB / 1MB，看比例如何变化（判据稳健性）。
"""
import sys,struct,collections,json,random
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,RAW,s['rawptr']),n
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not(nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'),pchd=w[i+4])
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
ck('L1a 基线',(len(COL),len(VT),sum(NS.values()))==(1214,1214,14044),(len(COL),len(VT),sum(NS.values())))
SL={vt:[P.dw(vt+4*k) for k in range(NS[vt])] for vt in VT}
def same_frac(s, sz):
    if len(s)<2: return None
    m=(1<<32)-sz
    return sum(1 for i in range(len(s)-1) if (s[i]&m)==(s[i+1]&m))/(len(s)-1)
allmult=[vt for vt in VT if NS[vt]>1]
ck('L2a 槽数 >1 的表数', True, len(allmult))
def wavg(sz):
    tot=0; wsum=0
    for vt in allmult:
        v=same_frac(SL[vt],sz)
        tot+=(NS[vt]-1); wsum+=v*(NS[vt]-1)
    return wsum/tot
for sz,name in ((4096,'4KB'),(65536,'64KB'),(1048576,'1MB')):
    f=wavg(sz)
    print('   L2b 页粒度 %s : 加权同页比例 = %.4f'%(name,f))
F4=wavg(4096)
ck('L2c 4KB 加权同页比例 > 0.5', F4>0.5, round(F4,4))
# L3 打乱反控
random.seed(20261128)
means=[]
for _ in range(20):
    tot=0;wsum=0
    for vt in allmult:
        s=SL[vt][:];random.shuffle(s)
        v=same_frac(s,4096)
        tot+=(NS[vt]-1);wsum+=v*(NS[vt]-1)
    means.append(wsum/tot)
mu=sum(means)/len(means)
ck('L3a 打乱后同页比例均值', True, round(mu,4))
ck('L3b 实测 >> 打乱（鉴别力）', F4>mu*1.5, (round(F4,4),round(mu,4),round(F4/mu,2)))
ck('L3c 打乱 20 次最大 < 实测', max(means)<F4, (round(max(means),4),round(F4,4)))
# L4 超长表
big=sorted([vt for vt in VT if NS[vt]>=128], key=lambda v:-NS[v])
rows=[]
for vt in big:
    s=SL[vt]; f=same_frac(s,4096)
    pages=[a&~0xFFF for a in s]
    runs=1
    for i in range(1,len(pages)):
        if pages[i]!=pages[i-1]: runs+=1
    rows.append(dict(vt=hex(vt),cls=COL[VT[vt]]['name'],n=NS[vt],same=round(f,4),pageruns=runs,
                     npages=len(set(pages))))
ck('L4a 超长表数', len(rows)==8, len(rows))
for r in rows: print('   L4b',r)
ck('L4c 超长表同页比例都 > 0.5', all(r['same']>0.5 for r in rows), [r['same'] for r in rows])
# L5 页号压缩序列
VT_C=0x7F5C70
s=SL[VT_C]; pages=[a&~0xFFF for a in s]
comp=[]
for p in pages:
    if comp and comp[-1][0]==p: comp[-1][1]+=1
    else: comp.append([p,1])
ck('L5a 0x7F5C70 页 run 数', True, len(comp))
print('   L5b 0x7F5C70 页 run 前 20:', [(hex(p),n) for p,n in comp[:20]])
ck('L5c 0x7F5C70 页 run 长度和==344', sum(n for p,n in comp)==344, sum(n for p,n in comp))
ck('L5d 最长页 run', True, max(n for p,n in comp))
# L6 每槽实现是否「同时被别的表当作同槽号」
res=dict(w4=round(F4,4),w64=round(wavg(65536),4),w1m=round(wavg(1048576),4),
         shuf_mean=round(mu,4),shuf_max=round(max(means),4),big=rows,
         comp7f5c70=[[hex(p),n] for p,n in comp],asserts=N,fails=fails)
json.dump(res,open('/home/t628/projects/ra2-campaign-forge/_r198/m4_locality.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
