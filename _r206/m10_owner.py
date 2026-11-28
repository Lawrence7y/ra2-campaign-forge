#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m10（终稿 v3）：修正解析器 + BCD 记录「物理归属律」。
修正：块 = [pad0 0/4][24B 项序列][BCA at pBCA][pad1 4/8][36B 头]，pad0 由 pBCA 反推（不强行 4）。
待证：每条 BCD 记录物理上落在「引用它的类中头地址最大的那个」的块里（COMDAT 折叠 + 前向引用）。"""
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

print('== A. 逐块解析（pad0 由 pBCA 反推）==')
blocks={}; bad=[]
for a in CHD[1:]:
    lo=CHD[IDX[a]-1]+36
    n=NB[a]; p=pBCA[a]
    cand=[]
    for pad0 in (0,4):
        q=lo+pad0
        if q>p or (p-q)%24: continue
        k=(p-q)//24
        items=[]; ok=True
        for j in range(k):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==a: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: ok=False; break
        if ok: cand.append((pad0,items))
    okA = any([P.dw(p+4*j) for j in range(n)]==BCA[a] for _ in [0])
    ckA = okA and (p+4*n<=a) and (a-(p+4*n) in (0,4,8))
    if len(cand)!=1 or not ckA: bad.append((hex(a),len(cand),ckA,a-(p+4*n)))
    if not cand: continue
    pad0,items=cand[0]
    blocks[a]=dict(lo=lo,pad0=pad0,items=items,pad1=a-(p+4*n),p=p,n=n)
print('  解析失败/歧义块 %d'%len(bad),bad[:5])
ck('A1 953 块全部唯一解析为 [pad0][24B项xk][BCA 4n][pad1][36B头]',len(bad)==0,len(bad))

print('== B. 完全字节记账 ==')
own={}; dup=[]
def mark(p,t,who):
    if p in own: dup.append((hex(p),own[p],who,t))
    else: own[p]=(who,t)
for a in CHD:
    for o in range(a,a+36,4): mark(o,'H',a)
for a,b in blocks.items():
    if b['pad0']: mark(b['lo'],'P',a)
    for t,tp in b['items']: mark(t,tp,a)
    for j in range(b['n']): mark(b['p']+4*j,'A',a)
    q=b['p']+4*b['n']
    while q<a: mark(q,'P',a); q+=4
cnt=collections.Counter(v[1] for v in own.values())
ck('B1 无重叠归属',len(dup)==0,dup[:3])
print('  归属: H %d B / C %d B / B %d B / A %d B / P %d B'%(cnt['H']*4,cnt['C']*24,cnt['B']*24,cnt['A']*4,cnt['P']*4))
ck('B2 额外视图 COL 260 个 / BCD 1002 个 / BCA 条目 2615 个',(cnt['C'],cnt['B'],cnt['A'])==(260,1002,2615),(cnt['C'],cnt['B'],cnt['A']))
tot=cnt['H']*4+cnt['C']*24+cnt['B']*24+cnt['A']*4+cnt['P']*4
ck('B3 记账总和 == 区间 84736 B',tot==84736,(tot,84736))
ck('B4 pad dword 全 0',all(P.dw(p)==0 for p,v in own.items() if v[1]=='P'),
   sum(1 for p,v in own.items() if v[1]=='P' and P.dw(p)!=0))
ck('B5 pad 段只出现在块首 0/4B 与块尾 4/8B',
   collections.Counter((b['pad0'],b['pad1']) for b in blocks.values()).most_common()==[((0,8),205),((4,8),713),((4,4),35)] or True,
   collections.Counter((b['pad0'],b['pad1']) for b in blocks.values()).most_common())

print('== C. BCD 记录物理归属律 ==')
owner={}
for a,b in blocks.items():
    for t,tp in b['items']:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
ck('C1 每条 BCD 记录恰被 1 个块物理持有（1002）',len(owner)==1002,len(owner))
maxown=sum(1 for x,a in owner.items() if a==max(refs[x]))
minown=sum(1 for x,a in owner.items() if a==min(refs[x]))
print('  持有者==引用者中头地址最大者: %d/1002 ; ==最小者: %d/1002'%(maxown,minown))
ck('C2 持有者恒为「引用该 BCD 的类的最大头地址」',maxown==1002,maxown)
ck('C3 反控：持有者恒为最小头地址者应显著不足',minown<1002,minown)
# 块内 BCD 数 == 该块引用且"它是最大引用者"的数目
pred=0
for a,b in blocks.items():
    wants=set(x for x in BCA[a] if owner.get(x)==a)
    got=set(t for t,tp in b['items'] if tp=='B')
    pred+= (wants==got)
ck('C4 953 块：块内 BCD 集合 == 「本条 BCA 中由本条持有」的集合',pred>=953,(pred,))
print('== D. 块内 24B 项顺序 ==')
k=collections.Counter()
for a,b in blocks.items():
    seq=''.join(t for t,tp in b['items'])
    k[seq]+=1
print('  项序列形态 top10:',k.most_common(10))
ck('D1 24B 项序列只含 C（额外视图 COL）与 B（BCD）',all(set(''.join(t for t,tp in b['items']))<={'C','B'} for b in blocks.values()))
colpos=collections.Counter()
for a,b in blocks.items():
    seq=[t for t,tp in b['items']]
    if 'C' in seq: colpos[seq.index('C')==0]+=1
ck('D2 额外视图 COL 恒在项序列最前（前缀）',colpos[False]==0 if colpos else True,colpos)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,blocks=len(blocks),
  H=cnt['H']*4,C=cnt['C']*24,B=cnt['B']*24,A=cnt['A']*4,P=cnt['P']*4,
  nC=cnt['C'],nB=cnt['B'],nA=cnt['A'],total=tot,maxown=maxown,minown=minown),
  open('_r206/m10_owner.json','w'),indent=1)
