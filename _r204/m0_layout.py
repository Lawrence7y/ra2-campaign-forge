#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m0：BCD/CHD 真实布局字节实证（先测后写；不出结论，只出原始字节+候选解释）。"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
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
        COL[base+4*i]=dict(sig=w[i],off=w[i+1],cd=w[i+2],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
print('COL',len(COL))
CHDs=sorted(set(v['pchd'] for v in COL.values()))
print('CHD distinct',len(CHDs))
print('CHD sample addrs',[hex(x) for x in CHDs[:5]])
# 取一个 CHD 原样 dump 32 字节
c0=CHDs[0]
print('\n--- CHD @%x raw 32B'%c0)
print(' '.join('%08x'%P.dw(c0+4*i) for i in range(8)))
for i in range(8):
    v=P.dw(c0+4*i)
    print('  +%02d %08x where=%s'%(4*i,v,P.where(v)))
# 找一个 n 与 arr 合理的解释
print('\n--- 全 954 CHD 上 +8/+12 解释检验')
n8=collections.Counter(); n12_in_sec=collections.Counter()
for c in CHDs:
    n8[P.dw(c+8)]+=1
    n12_in_sec[P.where(P.dw(c+12))]+=1
print('+8 分布 top10',n8.most_common(10),'<=200 计数',sum(v for k,v in n8.items() if k is not None and k<=200))
print('+12 所在段',n12_in_sec.most_common())
# BCD 布局：取第一个 CHD 的 BCA 第一个 BCD，dump 40 字节
arr=P.dw(c0+12); n=P.dw(c0+8)
print('\n--- CHD@%x n=%s arr=%x'%(c0,n,arr))
bcds=[P.dw(arr+4*j) for j in range(min(n,4) if n and n<10000 else 0)]
for b in bcds:
    print('BCD @%x raw40:'%b)
    for i in range(10):
        v=P.dw(b+4*i); 
        nm=P.cstr(v+8,300) if P.where(v) in ('.data','.rdata') else None
        print('   +%02d %08x  s32=%11d  where=%-8s %s'%(4*i,v,s32(v),P.where(v), (nm.decode('latin1') if nm and nm.startswith(b'.?A') else '')))
