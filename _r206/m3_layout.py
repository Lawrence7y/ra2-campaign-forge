#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m3：整段 RTTI 块的物理布局 —— 数组在 CHD 之前还是之后，块边界如何对齐。
正控：954 自指 +32；反控：把块基址整体 ±4/±8 位移后「数组严格落在前一条 gap 内」命中应塌。"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
PREV={a:(CHD[i-1] if i>0 else None) for i,a in enumerate(CHD)}
NEXT={a:(CHD[i+1] if i+1<len(CHD) else None) for i,a in enumerate(CHD)}
print('== A. 前 8 条 CHD 的 +0..+44 全字段 ==')
for a in CHD[:8]:
    print(' 0x%x name=%-42s'%(a,COL[G[a][0]]['name'][:42]))
    print('    +0..+44: %s'%[hex(P.dw(a+o) or 0) for o in range(0,48,4)])
    print('    prev=%s next=%s pBCA=%s n=%d'%(hex(PREV[a]) if PREV[a] else '-',hex(NEXT[a]) if NEXT[a] else '-',hex(P.dw(a+12)),P.dw(a+8)))
print('== B. pBCA 相对位置统计 ==')
k=collections.Counter()
for a in CHD:
    p=P.dw(a+12); pv=PREV[a]
    if p<a: k['before']+=1; k['in_prev_gap' if (pv is not None and p>=pv+40) else 'before_pv+40']+=1
    else: k['after']+=1
print(' ',k.most_common())
print('== C. 假设：块 = [BCD数组][BCA数组][40B 头]，数组落在前一条记录的 gap 内 ==')
ok=0; kk=collections.Counter()
for a in CHD:
    p=P.dw(a+12); n=P.dw(a+8); pv=PREV[a]; nx=NEXT[a]
    end=p+4*n
    good = (pv is not None) and (pv < p) and (end<=a)
    ok+=good
    kk[(good, a-p if p<a else None)]+=1
print(' 数组完全落在 (prev, a) 内: %d/954'%ok)
print(' 首 6 例 (prev,a,pBCA,eol):',[(hex(PREV[a]),hex(a),hex(P.dw(a+12)),hex(P.dw(a+12)+4*P.dw(a+8))) for a in CHD[1:7]])
print('== D. a - (prev + 40) == 本记录自己的前置字节数 ==')
dd=collections.Counter()
for a in CHD[1:]:
    dd[a-PREV[a]-40]+=1
print(' ',dd.most_common(12))
print('== E. 头 40B 之后到下一 CHD，字节由什么构成 ==')
for a in CHD[:6]:
    nx=NEXT[a]; seg=[hex(P.dw(a+o) or 0) for o in range(40,nx-a,4)]
    print('  0x%x L=%d tail40+=%s'%(a,nx-a,seg[:10]))
print('== F. +40 指向的 pTD 属于哪个类（与自身类名比对）==')
nm={a:COL[G[a][0]]['name'] for a in CHD}
tdof={}
for a in CHD: tdof[a]=P.dw(a+28)
inv=collections.defaultdict(list)
for a in CHD: inv[tdof[a]].append(a)
same=0; other=0; nottd=0; sam=collections.Counter()
for a in CHD:
    v=P.dw(a+40)
    if v in inv:
        if inv[v][0]==a: same+=1
        else: other+=1; sam[(nm[a].split('@@')[0],nm[inv[v][0]].split('@@')[0])]+=1
    else: nottd+=1
print(' +40==自身 pTD %d / ==他类 pTD %d / 非 pTD %d'%(same,other,nottd))
print(' 他类样例',[(x[0][:40],x[1][:40]) for x in list(sam)[:6]])
print('== G. +44 值分布与 numBase 关系 ==')
print(' ',collections.Counter(P.dw(a+44) for a in CHD).most_common(10))
print(' +44==numBase %d'%sum(1 for a in CHD if P.dw(a+44)==P.dw(a+8)))
print(' +44==0 且 L 分布',collections.Counter(NEXT[a]-a for a in CHD[:-1] if P.dw(a+44)==0).most_common(6))
