#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第七刀（主会话复算，修正 exec_b 的 COL 判据缺陷）：L 的 78 张虚表的**安装点**字节普查。
R193 已裁定：分裂主表/子表的是 COL d1（mdisp），不是 d0（d0 恒 0/1 只是 signature）。
X1 基线：COL 1214 / 主表(d1==0) 954 / 子表(d1!=0) 260 / 槽总 / L(d1==0 且链含 AbstractClass) 78。
X2 全 .text 的 C7 立即数安装点（四种形态），imm32 落在 L 表头集合内。
X3 归属函数起点（call/jmp 落点 ∪ >=2 连续 CC/90 之后），分布 + Top10。
X4 同一函数写 >=2 张 L 表头者（「一个构造/初始化器写多表」证据）。
X5 零命中 L 表头张数 + 这些表头作为任意立即数出现的计数。
X6 每个 L 表头的二级指针（.rdata/.data 里指向它的 dword）引用计数分布。
反控 N1 全部 1214 表头命中数；N2 表头地址作为任意立即数（不限于 C7）。
"""
import sys, re, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt,cap=600):
    k=0
    while k<cap and in_text(P.dw(vt+4*k)): k+=1
    return k
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
SUB=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
def chain(colva):
    c=COL[colva]; n=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12); out=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        if b is None or P.where(b) in ('None','other'): continue
        ptd=P.dw(b)
        if ptd is None: continue
        nm=P.cstr(ptd+8,160)
        out.append((nm.decode('latin1') if nm else None,P.dw(b+8)))
    return out
AB='.?AVAbstractClass@@'
LIN=sorted(vt for vt in MAIN if any(x[0]==AB for x in chain(VT[vt])))
ck('X1a COL=1214 主表=954 子表=260 L=78',
   (len(COL),len(MAIN),len(SUB),len(LIN))==(1214,954,260,780 if False else 78),
   (len(COL),len(MAIN),len(SUB),len(LIN)))
ck('X1b 槽总=14044',sum(nslot(v) for v in VT)==14044,sum(nslot(v) for v in VT))
Lset=set(LIN)
print('   L 表头（78）：')
print('   '+' '.join('%08X'%v for v in LIN))
# X2: C7 立即数扫描
o=P.r2o(LO); RAW=P.RAW; hits=[]
i=o; end=o+T['rawsize']
while i<end-10:
    b=RAW[i]
    va=LO+ (i-o)
    imm=None; form=None
    if b==0xC7:
        m=RAW[i+1]
        if m>>6==0 and (m&7)==5:   # C7 05 disp32 imm32
            imm=struct.unpack_from('<I',RAW,i+6)[0]; form='abs'
        elif (m&0xC7)==0x00 and (m>>3)==0:
            imm=struct.unpack_from('<I',RAW,i+2)[0]; form='mem'
        elif (m&0xC7)==0x40 and (m>>3)==0:
            imm=struct.unpack_from('<I',RAW,i+3)[0]; form='reg+disp8'
        elif (m&0xC7)==0x80 and (m>>3)==0:
            imm=struct.unpack_from('<I',RAW,i+6)[0]; form='reg+disp32'
    if imm is not None:
        hits.append((va,imm,form))
        i+=2
    else: i+=1
print('\n   C7 立即数（全部形态）总命中 %d' % len(hits))
li=[h for h in hits if h[1] in Lset]
print('   其中 imm32 落在 L 表头：%d 处' % len(li))
ck('X2a C7 命中 L 表头 > 0', len(li)>0, len(li))
for h in li[:40]: print('      %08X imm=%08X %s'%h)
json.dump([[h[0],h[1],h[2]] for h in li],open('_r195/m7_install_hits.json','w'))
print('\nFAILS=%d'%len(fails))
