#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第三刀：定位 m2 的两处结构性异常（不是判据错，是真实现象）。
A1 11 个 pTD 形态异常的 BCD 到底长什么样（m2 N2a 的 (991,11)）。
A2 260 个 COL 在其 CHD 内找不到 (pTD,mdisp) 全等 BCD —— 它们的 COL.mdisp / CHD / BCD 面各是什么。
A3 判定 A2 的成因：是「COL 找错（一个 vt 前有多个候选 COL）」还是「子表 COL 的 mdisp 不在 BCD 里」。
"""
import sys,struct,collections
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
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pdisp=s32(w[i+2]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
print('=== A2 COL.mdisp 分布（全 1214） ===')
print(dict(collections.Counter(c['mdisp'] for c in COL.values())))
print('=== A2 每个 COL 的 CHD 是否含其 (pTD,mdisp) ===')
stat=collections.Counter()
nomatch=[]
for c,cc in COL.items():
    lst=CHD[cc['pchd']]['bcds']
    same=[j for j,b in enumerate(lst) if P.dw(b)==cc['ptd']]
    md=[j for j in same if s32(P.dw(lst[j]+8))==cc['mdisp']]
    if md: stat['ok']+=1
    else:
        stat['nomatch']+=1; nomatch.append((c,cc,same,lst))
print(dict(stat))
print('=== A2 前 5 个 nomatch 明细 ===')
for c,cc,same,lst in nomatch[:5]:
    print(' COL %08X mdisp=%3d name=%s pCHD=%08X n=%d'%(c,cc['mdisp'],cc['name'],cc['pchd'],len(lst)))
    print('   同 pTD 的 BCD 下标:',same)
    print('   CHD 内 BCD 的 (局部名, mdisp):',[(P.cstr(P.dw(P.dw(b))+8,60).decode('latin1'),s32(P.dw(b+8))) for b in lst])
    print('   COL.pTD=%08X  CHD 内 pTD 集合=',hex(cc['ptd']),[hex(P.dw(b)) for b in lst])
print('=== A1 11 个 pTD 形态异常 ===')
bad=0
for v,d in CHD.items():
    for b in d['bcds']:
        td=P.dw(b); v0=P.dw(td); v1=P.dw(td+4); nm=P.cstr(td+8,80)
        ok = P.where(v0)=='.rdata' and v1==0 and nm and nm.startswith(b'.?A') and nm.endswith(b'@@')
        if not ok:
            bad+=1
            if bad<=11:
                print(' BCD %08X pTD=%08X attr=%d | td+0=%08X(%s) td+4=%08X td+8=%r'%(b,td,P.dw(b+20),v0,P.where(v0),v1,nm[:60] if nm else None))
print(' 异常总数=',bad)
