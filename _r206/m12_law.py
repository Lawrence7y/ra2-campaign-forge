#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m12（终稿 v5）：BCD 物理归属律 = 「地址上第一个大于该 BCD 的引用者」。
并把记账空洞逐一定位（差 8 B）。项序列 C 前缀律修正。"""
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
blocks={}
for a in CHD[1:]:
    lo=CHD[IDX[a]-1]+36; n=NB[a]; p=pBCA[a]
    for pad0 in (0,4):
        q=lo+pad0
        if q>p or (p-q)%24: continue
        items=[]
        for j in range((p-q)//24):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==a: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: items=None; break
        if items is not None and [P.dw(p+4*j) for j in range(n)]==BCA[a]:
            blocks[a]=dict(lo=lo,pad0=pad0,items=items,pad1=a-(p+4*n),p=p,n=n); break
own={}; dup=[]
def mark(p,t,who):
    if p in own: dup.append((hex(p),own[p],who,t))
    else: own[p]=(who,t)
for a in CHD:
    for o in range(a,a+36,4): mark(o,'H',a)
a0=CHD[0]
for j in range(NB[a0]): mark(pBCA[a0]+4*j,'A',a0)
for a,b in blocks.items():
    if b['pad0']: mark(b['lo'],'P',a)
    for t,tp in b['items']:
        ln=24
        for o in range(t,t+ln,4): mark(o,tp,a)
    for j in range(b['n']): mark(b['p']+4*j,'A',a)
    q=b['p']+4*b['n']
    while q<a: mark(q,'P',a); q+=4
cnt=collections.Counter(v[1] for v in own.values())
lo=min(own); hi=max(own)+4
holes=[o for o in range(lo,hi,4) if o not in own]
ck('A1 无重叠归属',len(dup)==0,dup[:3])
ck('A2 无空洞',len(holes)==0,[hex(x) for x in holes[:8]])
ck('A3 计数 260/1002/2615',(cnt['C'],cnt['B'],cnt['A'])==(260,1002,2615),(cnt['C'],cnt['B'],cnt['A']))
print('  记账: H %d B / C %d B / B %d B / A %d B / P %d B = %d B（区间 %d B）'%(
  cnt['H']*4,cnt['C']*24,cnt['B']*24,cnt['A']*4,cnt['P']*4,
  cnt['H']*4+cnt['C']*24+cnt['B']*24+cnt['A']*4+cnt['P']*4,hi-lo))
print('== B. 归属律 ==')
owner={}
for a,b in blocks.items():
    for t,tp in b['items']:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
def law(b):
    c=[y for y in refs[b] if y>b]
    return min(c) if c else None
ok=sum(1 for b in owner if owner[b]==law(b))
ck('B1 持有者 == min{引用者 y : y > BCD 地址} —— 1002/1002',ok==1002,ok)
bad=[b for b in owner if owner[b]!=law(b)]
print('  例外 %d'%len(bad))
for b in bad[:6]:
    print('   BCD 0x%x refs=%s law=%s own=0x%x'%(b,[hex(y) for y in refs[b]],
        hex(law(b)) if law(b) else None,owner[b]))
ck('B2 反控：改成 max 引用者命中率应 <100%',sum(1 for b in owner if owner[b]==max(refs[b]))<1002,
   sum(1 for b in owner if owner[b]==max(refs[b])))
ck('B3 反控：改成最近地址（|own-b| 最小）命中率',sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b)))<1002,
   sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b))))
print('== C. 块内 24B 项序列 ==')
seq=collections.Counter(''.join(tp for t,tp in b['items']) for b in blocks.values())
print('  形态 top12:',seq.most_common(12))
ck('C1 只含 C/B',all(set(s)<={'C','B'} for s in seq))
ck('C2 C 恒为前缀',all(s[:s.count('C')]=='C'*s.count('C') for s in seq),
   [s for s in seq if s[:s.count('C')]!='C'*s.count('C')][:5])
ck('C3 无 C 的块 %d 个 + 有 C 的 %d 个 = 953'%(
   sum(v for s,v in seq.items() if 'C' not in s),sum(v for s,v in seq.items() if 'C' in s)),
   sum(seq.values())==953)
print('== D. 反控 ==')
random.seed(206)
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (lo<=x<hi)]
ck('D1 区间外 3000 个 8 对齐随机地址满足完整头判据 0 个',
   sum(1 for x in random.sample(cands,3000) if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))==0)
ck('D2 全 .rdata「+0==0 且 +32==self」恰 954',sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if P.dw(x)==0 and P.dw(x+32)==x)==954)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,lo=hex(lo),hi=hex(hi),region=hi-lo,
  H=cnt['H']*4,C=cnt['C']*24,B=cnt['B']*24,A=cnt['A']*4,P=cnt['P']*4,
  nC=cnt['C'],nB=cnt['B'],nA=cnt['A'],law_ok=ok,law_bad=len(bad),
  seq=dict(seq.most_common(12))),open('_r206/m12_law.json','w'),indent=1)
