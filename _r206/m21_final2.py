#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m21（定稿 v3，订正 m20 的两条过强断言）：
订正说明：
  N1/N2 原断言「块起点位移 ±4 后无一可解析」**不成立且不应成立** —— 因为 pad0 是可选槽，
  位移 +4 恰好跳过 pad0 落到项序列，解析结果与真值同形。真正把起点钉死的是：
    ①24B 项必须 8 对齐（L1.2）②块区间无缝且无重叠的完全字节记账（L1.3/L1.4/L1.6）。
  因此必然性改由「字节记账唯一性」承担，不靠解析器歧义。
  X1/X2 原断言「a+36..+47 不含本条任何字段」过强 —— COMDAT 折叠使下一条块首 BCD 的 pTD
  也出现在本条 BCA 里（624 条）。正确的排除口径是「不等于本条自身地址 / 内嵌 COL / 本条 pTD / 本条 pBCA」。
"""
import sys,struct,collections,json
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); IDX={a:i for i,a in enumerate(CHD)}
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
TDOK=lambda td: P.where(td)=='.data' and (P.cstr(td+8,200) or b'').startswith(b'.?A')
def parse(n,lo):
    p=pBCA[n]; k=NB[n]
    for pad0 in (0,4):
        q=lo+pad0
        if q>p or (p-q)%24: continue
        items=[]
        for j in range((p-q)//24):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==n: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: items=None; break
        if items is None: continue
        if [P.dw(p+4*j) for j in range(k)]!=BCA[n]: continue
        e=p+4*k
        if n-e not in (4,8): continue
        return dict(lo=lo,pad0=pad0,q=q,items=items,p=p,n=k,pad1=n-e)
    return None
blocks={a:parse(a,CHD[IDX[a]-1]+36) for a in CHD[1:]}
blocks={a:b for a,b in blocks.items() if b}
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
print('== 1. 解析歧义的真实来源（订正 m20 N1/N2）==')
for d in (0,4,-4,8,-8):
    print('  起点偏移 %+d：可解析 %d/953'%(d,sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+d))))
ck('1.1 起点偏移 +4 仍可解析 748 条（=有 24B 项的块数），故解析器自身不能钉死起点',
   sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+4))==748,
   sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+4)))
ck('1.2 偏移 +4 后剩余的 205 条恰为 pad0==0 的块（起点本已 8 对齐）',
   all(blocks[a]['pad0']==0 for a in CHD[1:] if not parse(a,CHD[IDX[a]-1]+36+4)),
   sum(1 for a in CHD[1:] if not parse(a,CHD[IDX[a]-1]+36+4) and blocks[a]['pad0']==0))
ck('1.3 但偏移 +4 后 24B 项地址变成 8 非对齐（与 L1.2 冲突）⇒ 起点由对齐律唯一确定',
   all(parse(a,CHD[IDX[a]-1]+36+4) is None or all(t%8==4 for t,tp in parse(a,CHD[IDX[a]-1]+36+4)['items'])
       for a in CHD[1:]),
   sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+4) and any(t%8==0 for t,tp in parse(a,CHD[IDX[a]-1]+36+4)['items'])))
print('== 2. 尾部排除口径订正（m20 X1/X2）==')
v1=[(hex(a),i) for a in CHD[:-1] for i in range(3) if P.dw(a+36+4*i) in (a,a+16,P.dw(a+28),pBCA[a])]
ck('2.1 a+36..+47 无一值等于本条 自身地址/内嵌COL/本条pTD/本条pBCA',len(v1)==0,v1[:5])
v2=[(hex(a),i) for a in CHD[:-1] for i in range(3) if CHD[IDX[a]-1]+36<=P.dw(a+36+4*i)<a]
ck('2.2 无一值落本条块的物理区间 [prev+36, a)',len(v2)==0,v2[:5])
n624=sum(1 for a in CHD[:-1] if P.dw(a+40) in BCA[a])
ck('2.3 已知 624 条 +40 值同时出现在本条 BCA（COMDAT 折叠共享的 pTD），不构成反例',
   n624==624,n624)
ck('2.4 这 624 条的 +40 都指向「下一条块首 BCD 的 pTD」，不是本条的 BCD 地址',
   all(P.dw(a+40)==P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]) for a in CHD[:-1]
       if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items'] and blocks[CHD[IDX[a]+1]]['items'][0][1]=='B'),
   sum(1 for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items']
       and blocks[CHD[IDX[a]+1]]['items'][0][1]=='B'))
ck('2.5 +40 值从不等于本条任何 BCD 地址本身',all(P.dw(a+40) not in BCA[a] for a in CHD[:-1]),
   sum(1 for a in CHD[:-1] if P.dw(a+40) in BCA[a]))
print('== 3. 字节图标签（头后 3 dword 的四类形态）==')
byt={}
for a,b in blocks.items():
    q=b['lo']
    if b['pad0']: byt[q]='PAD0'; q+=4
    for t,tp in b['items']:
        for o in range(t,t+24,4): byt[o]=tp
    for j in range(b['n']): byt[b['p']+4*j]='A'
    for o in range(b['p']+4*b['n'],a,4): byt[o]='PAD1'
kinds=collections.Counter()
for a in CHD[:-1]:
    nb=blocks.get(CHD[IDX[a]+1])
    if nb: kinds[tuple(byt.get(nb['lo']+4*i,'?') for i in range(3))]+=1
print(' ',kinds.most_common(10))
ck('3.1 三 dword 形态恰 4 类且合计 953',
   sum(kinds.values())==953 and len(kinds)==4,(sum(kinds.values()),len(kinds)))
ck('3.2 四类计数 624/205/94/30',sorted(kinds.values(),reverse=True)==[624,205,94,30],sorted(kinds.values(),reverse=True))
ck('3.3 +36 仅在「下一条块无 24B 项」时非零（205+30=235 条），其余恒 0',
   sum(1 for a in CHD[:-1] if P.dw(a+36))==235,sum(1 for a in CHD[:-1] if P.dw(a+36)))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,kinds=dict((str(k),v) for k,v in kinds.most_common()),
  n624=n624,shift4=748),open('_r206/m21_final2.json','w'),indent=1)
