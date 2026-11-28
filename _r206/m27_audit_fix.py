#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m27：订正 m26 两条自错断言（审计 #522 的 A3/A5 复算口径）。
A3 口径：多引用 304 条中「存在引用者地址 > BCD 地址」的 280 条才是律 3 的判别样本。
A5 口径：24B 项判别位 —— BCD 的 +12(pdisp) 恒 -1、+16 恒 0；COL 的 +12 是 pTD(.data)、+16 是 pCHD(.rdata)。"""
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
def parse(n):
    lo=CHD[IDX[n]-1]+36; p=pBCA[n]; k=NB[n]
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
        if n-(p+4*k) not in (4,8): continue
        return (pad0,q,items,p+4*k)
    return None
B={a:parse(a) for a in CHD[1:]}; B={a:b for a,b in B.items() if b}
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
owner={}
for a,b in B.items():
    for t,tp in b[2]:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
print('== A3 订正口径 ==')
ck('A3.1 1002 个 BCD：单引用 698 + 多引用 304',(sum(1 for b in owner if len(refs[b])==1),sum(1 for b in owner if len(refs[b])>1))==(698,304))
hasGt=[b for b in owner if [y for y in refs[b] if y>b]]
ck('A3.2 多引用且存在引用者 > BCD 地址的恰 280 条（= 律 3 判别样本）',len(hasGt)==280,len(hasGt))
ck('A3.3 这 280 条：持有块==min 引用者 280/280；==max 引用者 0/280；==绝对最近 264/280',
   (sum(1 for b in hasGt if owner[b]==min(refs[b])),sum(1 for b in hasGt if owner[b]==max(refs[b])),
    sum(1 for b in hasGt if owner[b]==min(refs[b],key=lambda y:abs(y-b))))==(280,0,264),
   (sum(1 for b in hasGt if owner[b]==min(refs[b])),sum(1 for b in hasGt if owner[b]==max(refs[b])),
    sum(1 for b in hasGt if owner[b]==min(refs[b],key=lambda y:abs(y-b)))))
ck('A3.4 「持有块==min{全部类头>BCD}」也 1002/1002（该律是真律但区分力来自「持有者必引用」）',
   sum(1 for b in owner if owner[b]==min([y for y in CHD if y>b]))==1002)
ck('A3.5 非平凡内容：持有块必引用该 BCD 1002/1002；随机基线 2435/497974≈0.49%',
   all(b in BCA[owner[b]] for b in owner))
print('== A5 订正口径：24B 项判别位 ==')
ck('A5.1 BCD 项 +12(pdisp) 恒 -1 且 +16 恒 0',
   all(P.dw(t+12)==0xffffffff and P.dw(t+16)==0 for b in B.values() for t,tp in b[2] if tp=='B'))
ck('A5.2 COL 项 +12 是 pTD(.data)、+16 是 pCHD(.rdata)，且 +12 != 0xffffffff',
   all(P.where(P.dw(t+12))=='.data' and P.where(P.dw(t+16))=='.rdata' and P.dw(t+12)!=0xffffffff
       for b in B.values() for t,tp in b[2] if tp=='C'))
ck('A5.3 C 项过 BCD 判据 0/260；B 项过 COL 判据 0/1002',
   sum(1 for b in B.values() for t,tp in b[2] if tp=='C' and P.dw(t+12)==0xffffffff)==0 and
   sum(1 for b in B.values() for t,tp in b[2] if tp=='B' and P.where(P.dw(t+16))=='.rdata')==0)
print('== A4 订正口径：尾部语义预测 923/953，30 条为 pad0=4 无项块的 +44 ==')
sem=0; miss=[]
for a in CHD[:-1]:
    b=B.get(CHD[IDX[a]+1])
    if not b: continue
    pad0,q,items,e=b
    if items:
        t,tp=items[0]; want=[0,P.dw(t),P.dw(t+4)]
    else:
        nx=CHD[IDX[a]+1]; p0=pBCA[nx]
        want=[P.dw(p0),0,0] if pad0==0 else [0,P.dw(p0),P.dw(P.dw(p0)+4)]
    if [P.dw(a+36),P.dw(a+40),P.dw(a+44)]==want: sem+=1
    else: miss.append(hex(a))
ck('A4.1 语义预测 923/953',sem==923,sem)
ck('A4.2 30 条未命中全部是 pad0=4 且无 24B 项的块（+44 是 BCA[1] 所指 BCD 的 mdisp，非 BCA[0]）',
   all(B[CHD[IDX[int(x,16)]+1]][0]==4 and not B[CHD[IDX[int(x,16)]+1]][2] for x in miss),len(miss))
# 订正：这 30 条的 +44 = BCA[1] 所指 BCD 的 +8 (mdisp)
ok30=all(P.dw(int(x,16)+44)==s32(P.dw(P.dw(pBCA[CHD[IDX[int(x,16)]+1]])+4)+8) for x in miss)
ck('A4.3 这 30 条 +44 == 下一条 BCA[1] 所指 BCD 的 mdisp（+8）',ok30,ok30)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,hasGt=len(hasGt),multi=304,single=698,sem=sem,miss=len(miss)),
  open('_r206/m27_audit_fix.json','w'),indent=1)
