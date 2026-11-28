#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 探针 0：确定本轮两个目标的可复算基线。
 A 最长虚表（槽数）与 0x7F5C70 是否为其一；
 B CRC 状态对象调用面宿主集与「调用目标是函数入口」的集合规模；
 C .text 内 rep stosd / rep movsd 计数（判断零填充是否常见形态）。
所有数字一次输出，不做嵌套推断。
"""
import sys, struct, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n, P.RAW, s['rawptr']), n

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI

COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=struct.unpack('<i',struct.pack('<I',w[i+1]))[0],ptd=w[i+3],pchd=w[i+4],
                           name=nm.decode('latin1'))
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
ck('A1 COL==1214', len(COL)==1214, len(COL))
ck('A2 VT==1214', len(VT)==1214, len(VT))
ck('A3 槽总==14044', sum(NS.values())==14044, sum(NS.values()))
top=sorted(NS.items(), key=lambda kv:-kv[1])[:12]
print('   A4 最长 12 张表:', [(hex(v),n,COL[VT[v]]['name'],COL[VT[v]]['mdisp']) for v,n in top])
ck('A5 0x7F5C70 是表', 0x7F5C70 in NS, NS.get(0x7F5C70))
ck('A6 0x7F5C70 槽数==344', NS.get(0x7F5C70)==344, NS.get(0x7F5C70))
# 槽数分布
dist=collections.Counter(NS.values())
ck('A7 槽数 >=128 的表数', sum(v for k,v in dist.items() if k>=128), sum(v for k,v in dist.items() if k>=128))
print('   A8 槽数分布 top10:', dist.most_common(10))

# ---- B: 调用面
RAW=P.RAW
def r2o(va): return P.r2o(va)
def calls_to(fn):
    out=[]
    for va in range(LO,HI-5):
        if RAW[r2o(va)]!=0xE8: continue
        rel=struct.unpack_from('<i',RAW,r2o(va)+1)[0]
        if va+5+rel==fn: out.append(va)
    return out
CS=calls_to(0x4A1CA0)
ck('B1 0x4A1CA0 直接调用点==331', len(CS)==331, len(CS))
HOSTS=sorted({hex(v) for v in calls_to(0x410410)})
ck('B2 0x410410 调用点==27', len(HOSTS)==27, HOSTS)
ck('B3 0x410BE0 调用点', True, calls_to(0x410BE0))
# 全局 call 目标集合（近似函数入口集）
tg=set()
for va in range(LO,HI-5):
    if RAW[r2o(va)]==0xE8:
        rel=struct.unpack_from('<i',RAW,r2o(va)+1)[0]
        t=va+5+rel
        if LO<=t<HI: tg.add(t)
print('   B4 .text 内直接 call 目标数（近似入口集）:', len(tg))
ck('B5 0x410BE0 在入口集', 0x410BE0 in tg, 0x410BE0 in tg)

# ---- C: 串操作计数
b=RAW[r2o(LO):r2o(LO)+(HI-LO)]
ck('C1 .text 字节数', len(b)==(HI-LO), len(b))
nrep_stosd=sum(1 for i in range(len(b)-1) if b[i]==0xF3 and b[i+1]==0xAB)
nrep_movsd=sum(1 for i in range(len(b)-1) if b[i]==0xF3 and b[i+1]==0xA5)
nrep_stosb=sum(1 for i in range(len(b)-1) if b[i]==0xF3 and b[i+1]==0xAA)
ck('C2 rep stosd 计数', True, nrep_stosd)
ck('C3 rep movsd 计数', True, nrep_movsd)
ck('C4 rep stosb 计数', True, nrep_stosb)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
