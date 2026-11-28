#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m23（定稿，全部断言订正后）：MSVC RTTI 类块布局五律 —— 一次跑完全部证据。
五律（954 个类头、953 个块、1002 条 BCD 全量）：
 律1 块分解：块 = [pad0 0/4][24B 项 ×k][BCA 4n][pad1 4/8][36B 类头]；953/953 唯一解析。
 律2 对齐：24B 项恒 8 对齐；pBCA 8 对齐 ⟺ (k>=1 或 n>=2)，唯一例外 n==1 且 k==0（205 条）。
 律3 归属：BCD 物理持有块 == min{引用者类头 : 类头 > BCD 地址}，1002/1002。
 律4 尾部：类头后 12 字节完全由下一条块的字节图决定，四类形态 624/205/94/30。
 律5 记账：区间 0x7fa4b0..0x80efc4 = 84756 B 完全字节记账，无空洞无重叠。
正控：954 自指 a+32==a。反控：区间外随机 3000 地址 0 命中；律3 换 max/最近 <100%；错位 ±8 全崩。"""
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
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
blocks={}
for a in CHD[1:]:
    b=parse(a,CHD[IDX[a]-1]+36)
    if b: blocks[a]=b
print('== 正控 ==')
ck('C0 954 条自指 a+32==a',sum(1 for a in CHD if P.dw(a+32)==a)==954)
ck('C0b 954 条 a%8==0 且 a+0==0 且 内嵌COL(a+16).pCHD==a',
   all(a%8==0 and P.dw(a)==0 and COL[a+16]['pCHD']==a for a in CHD))
print('== 律1 块分解 ==')
ck('L1.1 953 块唯一可解析',len(blocks)==953,len(blocks))
ck('L1.2 24B 项恒 8 对齐',all(t%8==0 for b in blocks.values() for t,tp in b['items']))
ck('L1.3 pad0∈{0,4} / pad1∈{4,8}',all(b['pad0'] in (0,4) and b['pad1'] in (4,8) for b in blocks.values()),
   collections.Counter((b['pad0'],b['pad1']) for b in blocks.values()).most_common())
ck('L1.4 24B 项只含 C(额外视图COL)/B(BCD)',all(set(tp for t,tp in b['items'])<={'C','B'} for b in blocks.values()))
ck('L1.5 C 恒为前缀、C 数 == 该类视图数-1',
   all([tp for t,tp in b['items']]==['C']*sum(1 for t,tp in b['items'] if tp=='C')+['B']*sum(1 for t,tp in b['items'] if tp=='B') for b in blocks.values())
   and all(sum(1 for t,tp in b['items'] if tp=='C')==len(G[a])-1 for a,b in blocks.items()))
print('== 律2 对齐 ==')
al=collections.Counter((b['p']%8==0, len(b['items'])>=1 or b['n']>=2) for b in blocks.values())
ck('L2.1 pBCA 8 对齐 ⟺ (k>=1 或 n>=2)：953/953',al[(True,True)]+al[(False,False)]==953,al.most_common())
ex=[a for a,b in blocks.items() if b['p']%8]
ck('L2.2 例外恰 205 条且全为 n==1 且 k==0',len(ex)==205 and all(NB[a]==1 and not blocks[a]['items'] for a in ex))
ck('L2.3 (pBCA+4n)%8==0 ⇒ pad1==8；否则 pad1==4',
   all(b['pad1']==(8 if (b['p']+4*b['n'])%8==0 else 4) for b in blocks.values()),
   collections.Counter(((b['p']+4*b['n'])%8,b['pad1']) for b in blocks.values()).most_common())
print('== 律3 归属 ==')
owner={}
for a,b in blocks.items():
    for t,tp in b['items']:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
law=lambda b:(min([y for y in refs[b] if y>b]) if [y for y in refs[b] if y>b] else None)
ck('L3.1 持有块 == min{引用者类头 > BCD 地址}：1002/1002',sum(1 for b in owner if owner[b]==law(b))==1002,
   sum(1 for b in owner if owner[b]==law(b)))
ck('L3.2 反控 max 引用者 722',sum(1 for b in owner if owner[b]==max(refs[b]))==722)
ck('L3.3 反控 最近引用者 966',sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b)))==966)
ck('L3.4 单引用 698 条持有者==唯一引用者',sum(1 for b in owner if len(refs[b])==1 and owner[b]==refs[b][0])==698)
print('== 律4 尾部 ==')
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
ck('L4.1 尾部三 dword 形态恰 4 类，合计 953',sum(kinds.values())==953 and len(kinds)==4,(len(kinds),sum(kinds.values())))
ck('L4.2 四类计数 624/205/94/30',sorted(kinds.values(),reverse=True)==[624,205,94,30],sorted(kinds.values(),reverse=True))
print(' ',kinds.most_common())
ck('L4.3 (PAD0,B,B) 624 条：+36==0 且 +40==下一条块首 BCD 的 pTD 且 +44==其 numContained',
   all(P.dw(a+36)==0 and P.dw(a+40)==P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0])
       and P.dw(a+44)==P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]+4)
       for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items']
       and blocks[CHD[IDX[a]+1]]['items'][0][1]=='B'))
ck('L4.4 (PAD0,C,C) 94 条：+36==+40==0 且 +44==COL.mdisp',
   all(P.dw(a+36)==0 and P.dw(a+40)==0 and P.dw(a+44)==s32(P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]+4))
       for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items']
       and blocks[CHD[IDX[a]+1]]['items'][0][1]=='C'))
n235=[a for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and not blocks[CHD[IDX[a]+1]]['items']]
ck('L4.5 (A,PAD1,PAD1)+(PAD0,A,A) 235 条：+36 起即下一条 BCA 数组（首指针或 pad0 后的首指针）',
   all(P.dw(a+36)==P.dw(blocks[CHD[IDX[a]+1]]['p']) if blocks[CHD[IDX[a]+1]]['pad0']==0
       else (P.dw(a+36)==0 and P.dw(a+40)==P.dw(blocks[CHD[IDX[a]+1]]['p']))
       for a in n235),(len(n235),collections.Counter(blocks[CHD[IDX[a]+1]]['pad0'] for a in n235).most_common()))
print('== 律5 记账 ==')
own={}; dup=[]
def marklen(p,ln,t,who):
    for o in range(p,p+ln,4):
        if o in own: dup.append((hex(o),own[o],who,t))
        else: own[o]=(who,t)
for a in CHD: marklen(a,36,'H',a)
a0=CHD[0]; marklen(pBCA[a0],4*NB[a0],'A',a0); marklen(pBCA[a0]+4*NB[a0],a0-(pBCA[a0]+4*NB[a0]),'P',a0)
for a,b in blocks.items():
    if b['pad0']: marklen(b['lo'],4,'P',a)
    for t,tp in b['items']: marklen(t,24,tp,a)
    marklen(b['p'],4*b['n'],'A',a)
    marklen(b['p']+4*b['n'],b['pad1'],'P',a)
cnt=collections.Counter(v[1] for v in own.values()); lo=min(own); hi=max(own)+4
ck('L5.1 无重复归属',len(dup)==0,dup[:3])
ck('L5.2 无空洞',len([o for o in range(lo,hi,4) if o not in own])==0)
ck('L5.3 区间 0x%x..0x%x = 84756 B == 记账总和'%(lo,hi),hi-lo==sum(cnt.values())*4,(hi-lo,sum(cnt.values())*4))
ck('L5.4 各类字节 H 34344 / C 6240 / B 24048 / A 10460 / P 9664',
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P']*4)==(34344,6240,24048,10460,9664),
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P']*4))
ck('L5.5 pad 字节全 0',all(P.dw(p)==0 for p,v in own.items() if v[1]=='P'))
print('== 反控 ==')
random.seed(206)
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (lo<=x<hi)]
ck('R1 区间外 3000 随机 8 对齐地址满足完整头判据 0',sum(1 for x in random.sample(cands,3000)
   if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))==0)
ck('R2 全 .rdata「+0==0 且 +32==self」恰 954',sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8)
   if P.dw(x)==0 and P.dw(x+32)==x)==954)
ck('R3 头集整体 -8 位移后自指 0 命中',sum(1 for a in CHD if P.dw(a+24)==a)==0)
ck('R4 块起点整体 +8 ⇒ 可解析块 0 个',sum(1 for a in CHD[1:] if parse(a,CHD[IDX[a]-1]+36+8))==0)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,
  heads=len(CHD),blocks=len(blocks),lo=hex(lo),hi=hex(hi),region=hi-lo,
  H=cnt['H']*4,C=cnt['C']*4,B=cnt['B']*4,A=cnt['A']*4,P=cnt['P']*4,
  nC=260,nB=1002,nA=2615,kinds=dict((str(k),v) for k,v in kinds.most_common()),
  law3=sum(1 for b in owner if owner[b]==law(b)),law3_max=722,law3_near=966,law3_single=698,
  exception205=len(ex)),open('_r206/m23_definitive.json','w'),indent=1)
