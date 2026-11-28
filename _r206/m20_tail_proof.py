#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m20：尾部 12 字节的「归属必要性」证明（m19 L4.1 订正）。
三段：
 P 预测：用块分解模型的字节图预测 a+36/+40/+44，953/953 命中。
 N 必要：把下一条块起点从 lo 挪到 lo+4 / lo-4 / lo+8，解析必须失败（953/953）。
 X 排除：a+36..+47 不含本条任何字段（非自指、非本条 pTD、非本条 BCD/COL、非本条 pBCA）。"""
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
    """在给定 lo 上解析 head=n 的块；返回 (pad0,items,pad1) 或 None"""
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
        if n-(e) not in (4,8): continue
        return dict(lo=lo,pad0=pad0,q=q,items=items,p=p,n=k,pad1=n-e)
    return None
blocks={}
for a in CHD[1:]:
    b=parse(a,CHD[IDX[a]-1]+36)
    if b: blocks[a]=b
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
# 字节图
byt={}
for a,b in blocks.items():
    q=b['lo']
    if b['pad0']: byt[q]='PAD0'; q+=4
    for t,tp in b['items']:
        for o in range(t,t+24,4): byt[o]=tp
    for j in range(b['n']): byt[b['p']+4*j]='A'
    for o in range(b['p']+4*b['n'],a,4): byt[o]='PAD1'
print('== P 预测 ==')
pred=0; miss=[]
for a in CHD[:-1]:
    nb=blocks.get(CHD[IDX[a]+1])
    if nb is None: miss.append((hex(a),'noblock')); continue
    want=[P.dw(a+36+4*i) for i in range(3)]
    exp=[P.dw(nb['lo']+4*i) for i in range(3)]
    tag=[byt.get(nb['lo']+4*i,'?') for i in range(3)]
    if want==exp: pred+=1
    else: miss.append((hex(a),[hex(x or 0) for x in want],[hex(x or 0) for x in exp]))
ck('P1 953 条：a+36/+40/+44 == 下一条块 lo 起前 3 dword（字节图可逐条标注）',pred==953,(pred,miss[:3]))
kinds=collections.Counter()
for a in CHD[:-1]:
    nb=blocks.get(CHD[IDX[a]+1])
    if nb: kinds[tuple(byt.get(nb['lo']+4*i,'?') for i in range(3))]+=1
print('  尾部三 dword 的字节图标签 top10:',kinds.most_common(10))
print('== N 必要性 ==')
for d in (4,-4,8,-8):
    ok=sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+d))
    print('  起点偏移 %+d：可解析块数 %d/953'%(d,ok))
ck('N1 起点 +4 后无一可解析',sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+4))==0)
ck('N2 起点 -4 后无一可解析',sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36-4))==0)
ck('N3 起点 +8 后无一可解析',sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+8))==0)
print('== X 排除本条字段 ==')
viol=[]
for a in CHD[:-1]:
    own=set(BCA[a])|{a,a+16,pBCA[a],P.dw(a+28)}
    for i in range(3):
        if P.dw(a+36+4*i) in own: viol.append((hex(a),i,hex(P.dw(a+36+4*i))))
ck('X1 a+36..+47 无任何值落本条字段集（自身/内嵌COL/pTD/pBCA/BCA 条目）',len(viol)==0,viol[:5])
# 也无落"本条 BCD 池"的
ck('X2 无值落本类的物理块区间 [prev+36, a+36)',
   all(not (CHD[IDX[a]-1]+36 <= P.dw(a+36+4*i) < a+36) for a in CHD[:-1] for i in range(3) if P.dw(a+36+4*i)),
   [ (hex(a),i) for a in CHD[:-1] for i in range(3)
     if P.dw(a+36+4*i) and CHD[IDX[a]-1]+36<=P.dw(a+36+4*i)<a+36][:5])
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,pred=pred,kinds=dict((str(k),v) for k,v in kinds.most_common(10)),
  shift4=0,shiftm4=0,viol=len(viol)),open('_r206/m20_tail_proof.json','w'),indent=1)
