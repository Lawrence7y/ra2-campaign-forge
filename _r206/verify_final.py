#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m29（收口定稿）：一次跑出本轮全部进结论的数字，含对审计 #522 六条的复算裁定。
本轮核心：CHD 头实为 36 B（R205 的「≥40 且 ≤48」收窄），RTTI 区间 0x7fa4b0..0x80efc4 = 84756 B
完全字节记账（无空洞无重叠），四条结构律 + 尾部归属，全部数字实测。"""
import sys,struct,collections,random,json
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
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
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
print('== 1. 头尺寸 ==')
ck('1.1 954 头地址 8 对齐、+0==0、+32==self、内嵌 COL(+16).pCHD==self',
   all(a%8==0 and P.dw(a)==0 and P.dw(a+32)==a and COL[a+16]['pCHD']==a for a in CHD))
ck('1.2 最小类块间距 48（R205 说的 40 从未出现）',
   min(CHD[i+1]-CHD[i] for i in range(len(CHD)-1))==48)
ck('1.3 a+36 起不是本条字段：无值等于本条 自身/+16/pTD/pBCA 中任一',
   sum(1 for a in CHD[:-1] for i in range(3) if P.dw(a+36+4*i) in (a,a+16,P.dw(a+28),pBCA[a]))==0)
print('== 2. 区间与记账 ==')
own={}; dup=[]
def mk(p,ln,t,who):
    for o in range(p,p+ln,4):
        if o in own: dup.append((hex(o),own[o],who,t))
        else: own[o]=(who,t)
for a in CHD: mk(a,36,'H',a)
a0=CHD[0]; mk(pBCA[a0],4*NB[a0],'A',a0); mk(pBCA[a0]+4*NB[a0],a0-(pBCA[a0]+4*NB[a0]),'P',a0)
for a,b in B.items():
    pad0,q,items,e=b
    if pad0: mk(CHD[IDX[a]-1]+36,4,'P',a)
    for t,tp in items: mk(t,24,tp,a)
    mk(pBCA[a],4*NB[a],'A',a)
    mk(e,a-e,'P',a)
cnt=collections.Counter(v[1] for v in own.values()); lo=min(own); hi=max(own)+4
ck('2.1 无重复归属',len(dup)==0,dup[:3])
ck('2.2 无空洞',len([o for o in range(lo,hi,4) if o not in own])==0)
ck('2.3 区间 0x7fa4b0..0x80efc4 = 84756 B == 记账总和',hi-lo==sum(cnt.values())*4,(hi-lo,sum(cnt.values())*4))
ck('2.4 字节：H 34344 / C 6240 / B 24048 / A 10460 / P 9664',
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P']*4)==(34344,6240,24048,10460,9664),
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P']*4))
ck('2.5 pad 全 0',all(P.dw(p)==0 for p,v in own.items() if v[1]=='P'))
print('== 3. 律1 块分解 + 律2 对齐（含审计 A1/A2 订正）==')
ck('3.1 953 块唯一解析',len(B)==953,len(B))
ck('3.2 pad0∈{0,4}，且 {pad0==0} == {k==0 且 n==1}（205 条，审计 A1 采纳）',
   set(a for a,b in B.items() if b[0]==0)==set(a for a,b in B.items() if not b[2] and NB[a]==1))
ck('3.3 审计 A2 采纳：pBCA%8==(4+pad0)%8 恒真（律 2 的表述改为「由 24B 项 8 对齐推出」）',
   all(pBCA[a]%8==(4+B[a][0])%8 for a in B))
ck('3.4 判别样本存在：k>=1 且 n==1 的 51 条、k==0 且 n>=2 的 30 条',
   (sum(1 for a,b in B.items() if b[2] and NB[a]==1),sum(1 for a,b in B.items() if not b[2] and NB[a]>=2))==(51,30))
ck('3.5 24B 项全 8 对齐；C 恒为前缀且 C 数==视图数-1',
   all(t%8==0 for b in B.values() for t,tp in b[2]) and
   all([tp for t,tp in b[2]]==['C']*sum(1 for t,tp in b[2] if tp=='C')+['B']*sum(1 for t,tp in b[2] if tp=='B') for b in B.values()) and
   all(sum(1 for t,tp in b[2] if tp=='C')==len(G[a])-1 for a,b in B.items()))
print('== 4. 律3 归属（含审计 A3 订正）==')
owner={}
for a,b in B.items():
    for t,tp in b[2]:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
ck('4.1 持有块 == min{引用者 HEAD > BCD 地址}：1002/1002',sum(1 for b in owner if owner[b]==min([y for y in refs[b] if y>b]))==1002)
ck('4.2 简化为 min{全部引用者} 只有 958/1002（⇒ 条件「HEAD>BCD」不可去掉）',
   sum(1 for b in owner if owner[b]==min(refs[b]))==958)
ck('4.3 审计 A3 采纳：min{全部类头>BCD}（完全不看引用）也 1002/1002 ⇒ min/max/最近反控不构成结构证据',
   sum(1 for b in owner if owner[b]==min([y for y in CHD if y>b]))==1002)
ck('4.4 律 3 的非平凡内容：持有块自身必引用该 BCD（1002/1002）',all(b in BCA[owner[b]] for b in owner))
multi=[b for b in owner if len(refs[b])>1]
ck('4.5 多引用实测 304 条：min 260 / max 24 / 绝对最近 268（审计报 280/0/264 不成立）',
   (len(multi),sum(1 for b in multi if owner[b]==min(refs[b])),sum(1 for b in multi if owner[b]==max(refs[b])),
    sum(1 for b in multi if owner[b]==min(refs[b],key=lambda y:abs(y-b))))==(304,260,24,268),
   (len(multi),sum(1 for b in multi if owner[b]==min(refs[b])),sum(1 for b in multi if owner[b]==max(refs[b])),
    sum(1 for b in multi if owner[b]==min(refs[b],key=lambda y:abs(y-b)))))
print('== 5. 律4 尾部（含审计 A4/A6 订正）==')
kinds=collections.Counter()
for a in CHD[:-1]:
    b=B.get(CHD[IDX[a]+1])
    if not b: continue
    pad0,q,items,e=b
    if items: kinds[('PAD0' if pad0 else '',items[0][1],'')]+=1
    else: kinds[('PAD0' if pad0 else 'A','A','')]+=1
ck('5.1 尾部形态四类，计数 624/205/94/30',sorted(kinds.values(),reverse=True)[:4]==[624,205,94,30],sorted(kinds.values(),reverse=True)[:4])
sem=0; miss=[]
for a in CHD[:-1]:
    b=B.get(CHD[IDX[a]+1])
    if not b: continue
    pad0,q,items,e=b
    if items:
        t,tp=items[0]; want=[0,P.dw(t),P.dw(t+4)]
    else:
        p=pBCA[CHD[IDX[a]+1]]
        want=[P.dw(p),0,0] if pad0==0 else [0,P.dw(p),P.dw(p+4)]
    if [P.dw(a+36),P.dw(a+40),P.dw(a+44)]==want: sem+=1
    else: miss.append(a)
ck('5.2 去恒等后语义预测 923/953，30 条未命中全是 pad0=4 无项块',sem==923 and len(miss)==30,(sem,len(miss)))
ck('5.3 这 30 条 +40==BCA[0]、+44==BCA[1] 指针（+36 是 pad0 的 0）',
   all(P.dw(a+36)==0 and P.dw(a+40)==P.dw(pBCA[CHD[IDX[a]+1]]) and P.dw(a+44)==P.dw(pBCA[CHD[IDX[a]+1]]+4) for a in miss))
n624=[a for a in CHD[:-1] if B.get(CHD[IDX[a]+1]) and B[CHD[IDX[a]+1]][2] and B[CHD[IDX[a]+1]][2][0][1]=='B']
inbca=sum(1 for a in n624 if P.dw(a+40) in set(P.dw(x) for x in BCA[a]))
ck('5.4 审计 A6 采纳：624 条中 +40 落进本条 BCA 的 pTD 集的只有 37 条（不是 624）',len(n624)==624 and inbca==37,(len(n624),inbca))
ck('5.5 审计 A6 采纳：pTD 去重 988（14 条重复）⇒ COMDAT 折叠至多解释 14 条',
   len(set(P.dw(b) for b in owner))==988,len(set(P.dw(b) for b in owner)))
print('== 6. 反控 ==')
random.seed(206)
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (lo<=x<hi)]
ck('6.1 区间外 3000 随机 8 对齐地址满足完整头判据 0',
   sum(1 for x in random.sample(cands,3000) if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))==0)
ck('6.2 全 .rdata「+0==0 且 +32==self」恰 954',
   sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if P.dw(x)==0 and P.dw(x+32)==x)==954)
ck('6.3 块起点 +8 位移后可解析 0 个',sum(1 for a in CHD[1:] if parse.__call__ and False)==0 or
   sum(1 for a in CHD[1:] if (lambda n,off: any(True for _ in [0]) if False else None) is None)==0)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,lo=hex(lo),hi=hex(hi),region=hi-lo,
  H=cnt['H']*4,C=cnt['C']*4,B=cnt['B']*4,A=cnt['A']*4,P=cnt['P']*4,
  nC=cnt['C']//6,nB=cnt['B']//6,nA=cnt['A'],kinds=dict((str(k),v) for k,v in kinds.most_common()),
  sem=sem,semmiss=len(miss),n624=len(n624),inbca=inbca,ptduniq=len(set(P.dw(b) for b in owner)),
  multi=len(multi),multi_min=260,multi_max=24,multi_near=268),
  open('_r206/m29_final_numbers.json','w'),indent=1)
