#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m0 侦察：CHD 记录跨度与 +16 之后是否还有字段（R204 未取得项④）。不产结论，只测数。"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
print('CHD count',len(CHD),'range 0x%x..0x%x'%(CHD[0],CHD[-1]))
# 相邻 CHD 间距
gaps=collections.Counter(CHD[i+1]-CHD[i] for i in range(len(CHD)-1))
print('gap dist top12',gaps.most_common(12))
print('gap ==16 cnt',gaps[16],'gap>16 cnt',sum(c for g,c in gaps.items() if g>16))
# +16 之后的字节形态
shape=collections.Counter()
for a in CHD:
    for off in (16,20,24,28,32,36,40,44):
        v=P.dw(a+off)
        shape[off]=shape.get(off,0)
# 逐 off 分类
for off in (16,20,24,28,32,36,40,44):
    k=collections.Counter()
    for a in CHD:
        v=P.dw(a+off)
        if v is None: k['none']+=1
        elif v==0: k['zero']+=1
        elif in_text(v): k['text']+=1
        elif v in COL: k['COL']+=1
        elif v in G: k['CHD']+=1
        else: k[P.where(v)]+=1
    print('  +%d %s'%(off,k.most_common(6)))
# 间距>16 的那些 CHD，中间 16..gap 的字节
big=[(CHD[i],CHD[i+1]) for i in range(len(CHD)-1) if CHD[i+1]-CHD[i]>16]
print('big gaps',len(big),big[:8])
for a,b in big[:5]:
    print('  CHD 0x%x name=%s gap=%d bytes16..=%s'%(a,COL[G[a][0]]['name'][:40],b-a,
          [hex(P.dw(a+o)) for o in range(16,min(b-a,64),4)]))
# 末尾 CHD 之后
a=CHD[-1]
print('last CHD 0x%x, +16..+64 ='%a,[hex(P.dw(a+o)) for o in range(16,64,4)])
