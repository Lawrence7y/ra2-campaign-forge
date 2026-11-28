#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m19（定稿 v2）：RTTI 块三条结构律 + 尾部字段归属律，一次跑完全部证据。
律 1（块分解）：类块 = [pad0][24B 项 x k][BCA 4n][pad1][36B 头]，953/953 唯一解析。
律 2（对齐）：24B 项恒 8 对齐；pBCA 8 对齐 <=> (k>=1 或 n>=2)，唯一例外 n==1 且 k==0（205 条）。
律 3（归属）：BCD 物理持有块 == min{引用者 HEAD : HEAD > BCD 地址}，1002/1002。
律 4（尾部）：a+36/+40/+44 完全可由下一条块的解析预测（953/953），不含本条任何字段。
正控：954 自指 +32。反控：区间外随机地址 0 命中；律 3 换 max/最近均 <100%；错位 ±4/±8 崩。"""
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
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
# 块解析
blocks={}
for a in CHD[1:]:
    lo=CHD[IDX[a]-1]+36; n=NB[a]; p=pBCA[a]
    sols=[]
    for pad0 in (0,4):
        q=lo+pad0
        if q>p or (p-q)%24: continue
        items=[]
        for j in range((p-q)//24):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==a: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: items=None; break
        if items is None: continue
        if [P.dw(p+4*j) for j in range(n)]!=BCA[a]: continue
        if a-(p+4*n) not in (4,8): continue
        sols.append((pad0,q,items,p+4*n))
    if len(sols)==1:
        pad0,q,items,e=sols[0]
        blocks[a]=dict(lo=lo,pad0=pad0,q=q,items=items,p=p,n=n,pad1=a-e)
print('== 律 1：唯一解析 ==')
ck('L1.1 953 块唯一解析',len(blocks)==953,len(blocks))
ck('L1.2 24B 项全 8 对齐',all(t%8==0 for b in blocks.values() for t,tp in b['items']))
# 记账
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
ck('L1.3 无重叠归属',len(dup)==0,dup[:3])
ck('L1.4 无空洞',len([o for o in range(lo,hi,4) if o not in own])==0)
ck('L1.5 字节记账 34344/6240/24048/10460 + pad 9664 = 84756 且 == 区间跨度',
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P']*4)==(34344,6240,24048,10460,9664),
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P']*4))
ck('L1.6 区间跨度 0x%x..0x%x = 84756'%(lo,hi),hi-lo==84756,hi-lo)
ck('L1.7 pad 字节全 0',all(P.dw(p)==0 for p,v in own.items() if v[1]=='P'))
print('== 律 2：对齐 ==')
al=collections.Counter()
for a,b in blocks.items(): al[(b['p']%8==0, len(b['items'])>=1 or b['n']>=2)]+=1
ck('L2.1 pBCA 8 对齐 <=> (k>=1 或 n>=2)：953/953',al[(True,True)]+al[(False,False)]==953,al.most_common())
ex=[a for a,b in blocks.items() if b['p']%8==4]
ck('L2.2 例外恰为 n==1 且 k==0 的 205 条',len(ex)==205 and all(NB[a]==1 and not blocks[a]['items'] for a in ex),
   (len(ex),collections.Counter((NB[a],len(blocks[a]['items'])) for a in ex).most_common(3)))
ck('L2.3 pad1 ∈{4,8} 且 (pBCA+4n)%8==0 ⇒ pad1==8',
   all(b['pad1'] in (4,8) for b in blocks.values()) and
   all(b['pad1']==8 for b in blocks.values() if (b['p']+4*b['n'])%8==0),
   collections.Counter(((b['p']+4*b['n'])%8,b['pad1']) for b in blocks.values()).most_common())
ck('L2.4 lo=prev+36 恒 ≡4 (mod 8)，头恒 8 对齐',set(b['lo']%8 for b in blocks.values())=={4} and all(a%8==0 for a in CHD))
print('== 律 3：BCD 物理归属 ==')
owner={}
for a,b in blocks.items():
    for t,tp in b['items']:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
law=lambda b:(min([y for y in refs[b] if y>b]) if [y for y in refs[b] if y>b] else None)
ck('L3.1 持有块 == min{HEAD>BCD 的引用者}：1002/1002',sum(1 for b in owner if owner[b]==law(b))==1002,
   sum(1 for b in owner if owner[b]==law(b)))
ck('L3.2 反控 max 引用者 722',sum(1 for b in owner if owner[b]==max(refs[b]))==722,
   sum(1 for b in owner if owner[b]==max(refs[b])))
ck('L3.3 反控 最近引用者 966',sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b)))==966,
   sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b))))
ck('L3.4 单引用 698 条持有者==唯一引用者',sum(1 for b in owner if len(refs[b])==1 and owner[b]==refs[b][0])==698)
print('== 律 4：尾部三字段可由下一条块预测 ==')
pred=0; miss=[]
for a in CHD[:-1]:
    nb=blocks.get(CHD[IDX[a]+1])
    want=[0,0,0]
    if nb is None: miss.append((hex(a),'no-block')); continue
    if nb['items']:
        t,tp=nb['items'][0]
        want=[0, P.dw(t) if tp=='B' else P.dw(t), P.dw(t+4)]
    else:
        want=[P.dw(nb['p']), P.dw(P.dw(nb['p'])), P.dw(P.dw(nb['p'])+4)]
    got=[P.dw(a+36),P.dw(a+40),P.dw(a+44)]
    if got==want: pred+=1
    else: miss.append((hex(a),[hex(x or 0) for x in got],[hex(x or 0) for x in want]))
ck('L4.1 953 条尾部三字段全部由下一条块解析预测成功',pred==953,(pred,miss[:3]))
ck('L4.2 首项 BCD(624)：+40==BCD.pTD(.data) 且 +44==BCD.numContained',
   all(P.dw(a+40)==P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]) and P.where(P.dw(a+40))=='.data'
       for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items']
       and blocks[CHD[IDX[a]+1]]['items'][0][1]=='B'))
ck('L4.3 首项额外COL(94)：+36==+40==0 且 +44==COL.mdisp',
   all(P.dw(a+36)==0 and P.dw(a+40)==0 and P.dw(a+44)==s32(P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]+4))
       for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items']
       and blocks[CHD[IDX[a]+1]]['items'][0][1]=='C'),
   sum(1 for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items']
       and blocks[CHD[IDX[a]+1]]['items'][0][1]=='C'))
ck('L4.4 无 24B 项(235)：+36 起即下一条 BCA 数组首指针',
   all(P.dw(a+36)==P.dw(blocks[CHD[IDX[a]+1]]['p']) if blocks[CHD[IDX[a]+1]]['p']==a+36
       else P.dw(a+36)==0 for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and not blocks[CHD[IDX[a]+1]]['items']))
print('== 反控 ==')
random.seed(206)
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (lo<=x<hi)]
ck('E1 区间外 3000 随机 8 对齐地址满足完整头判据 0',sum(1 for x in random.sample(cands,3000)
   if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))==0)
ck('E2 全 .rdata「+0==0 且 +32==self」恰 954',sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8)
   if P.dw(x)==0 and P.dw(x+32)==x)==954)
ck('E3 头集 +4 位移自指 0 命中',sum(1 for a in CHD if P.dw(a+36)==a)==0)
ck('E4 头集 -4 位移自指 0 命中',sum(1 for a in CHD if P.dw(a+28)==a)==0)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,blocks=953,lo=hex(lo),hi=hex(hi),region=hi-lo,
  H=cnt['H']*4,C=cnt['C']*4,B=cnt['B']*4,A=cnt['A']*4,P=cnt['P']*4,
  nC=260,nB=1002,nA=2615,law3=sum(1 for b in owner if owner[b]==law(b)),law3_max=722,law3_near=966,
  tail_pred=pred,kind=dict(collections.Counter(
     blocks[CHD[IDX[a]+1]]['items'][0][1] if blocks.get(CHD[IDX[a]+1]) and blocks[CHD[IDX[a]+1]]['items'] else 'none'
     for a in CHD[:-1]).most_common())),open('_r206/m19_law_final.json','w'),indent=1)
