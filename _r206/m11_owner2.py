#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m11（终稿 v4）：物理归属律细分类 + 区间端点订正。
订正：RTTI 区间 = [首条 BCA 数组 0x7fa4b0, 末条头+36 0x80efc4) = 84756 B（不是 84736）。
归属律：BCD 记录物理落在「引用它的类里**头地址最小**的那个」的块内（958/1002），44 例外细查。"""
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
        items=[];
        for j in range((p-q)//24):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==a: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: items=None; break
        if items is not None and [P.dw(p+4*j) for j in range(n)]==BCA[a]:
            blocks[a]=dict(lo=lo,pad0=pad0,items=items,pad1=a-(p+4*n),p=p,n=n); break
print('== A. 完全记账（区间 0x7fa4b0..0x80efc4）==')
own={}; dup=[]
def mark(p,t,who):
    if p in own: dup.append((hex(p),own[p],who,t))
    else: own[p]=(who,t)
for a in CHD:
    for o in range(a,a+36,4): mark(o,'H',a)
# 首条类的 BCA 数组在区间起点前（无前驱块）
a0=CHD[0]
for j in range(NB[a0]): mark(pBCA[a0]+4*j,'A',a0)
for a,b in blocks.items():
    if b['pad0']: mark(b['lo'],'P',a)
    for t,tp in b['items']: mark(t,tp,a)
    for j in range(b['n']): mark(b['p']+4*j,'A',a)
    q=b['p']+4*b['n']
    while q<a: mark(q,'P',a); q+=4
cnt=collections.Counter(v[1] for v in own.values())
lo=min(own); hi=max(own)+4
ck('A1 无重叠归属',len(dup)==0,dup[:3])
ck('A2 区间 [0x%x,0x%x) = %d B 与记账总和一致'%(lo,hi,hi-lo),hi-lo==cnt['H']*4+cnt['C']*24+cnt['B']*24+cnt['A']*4+cnt['P']*4,
   (hi-lo,cnt['H']*4+cnt['C']*24+cnt['B']*24+cnt['A']*4+cnt['P']*4))
print('  归属: H 头36Bx954=%d / C 额外COL 24Bx%d=%d / B BCD 24Bx%d=%d / A BCA 4Bx%d=%d / P pad 4Bx%d=%d'%(
  cnt['H']*4,cnt['C'],cnt['C']*24,cnt['B'],cnt['B']*24,cnt['A'],cnt['A']*4,cnt['P'],cnt['P']*4))
ck('A3 计数 260/1002/2615',(cnt['C'],cnt['B'],cnt['A'])==(260,1002,2615),(cnt['C'],cnt['B'],cnt['A']))
ck('A4 区间内每个 dword 都被归属（无空洞）',len([o for o in range(lo,hi,4) if o not in own])==0)
ck('A5 pad dword 全 0',all(P.dw(p)==0 for p,v in own.items() if v[1]=='P'))

print('== B. BCD 物理归属律 ==')
owner={}
for a,b in blocks.items():
    for t,tp in b['items']:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
multi=[x for x in owner if len(refs[x])>1]
print(' BCD 1002 条：单引用 %d，多引用 %d'%(1002-len(multi),len(multi)))
ck('B1 单引用 BCD 的持有者必是唯一引用者',all(owner[x]==refs[x][0] for x in owner if len(refs[x])==1),
   sum(1 for x in owner if len(refs[x])==1 and owner[x]!=refs[x][0]))
ck('B2 多引用 BCD 的持有者 == 头地址最小的引用者',
   all(owner[x]==min(refs[x]) for x in multi),
   collections.Counter(owner[x]==min(refs[x]) for x in multi))
badm=[x for x in multi if owner[x]!=min(refs[x])]
print('  例外 %d 条'%len(badm))
for x in badm[:8]:
    print('   BCD 0x%x pTD=%s 引用者=%s 持有块=0x%x'%(x,P.cstr(P.dw(x)+8,60),
        [hex(y) for y in refs[x]],owner[x]))
# 例外的共同点：持有者是否为引用者的「前一个块」
k=collections.Counter()
for x in badm:
    idx=[IDX[y] for y in refs[x]]
    k[(owner[x]==max(refs[x]), x<min(refs[x]))]+=1
print('  例外分类 (持有==最大引用, BCD地址<最小引用者):',k.most_common())
print('== C. 块内 24B 项序列 ==')
seq=collections.Counter(''.join(t for t,tp in b['items']) for b in blocks.values())
print('  形态 top12:',seq.most_common(12))
ck('C1 项序列只含 C/B 两字符',all(set(s)<={'C','B'} for s in seq))
ck('C2 C 恒为前缀',all(s=='' or s.count('C')==0 or s[:s.count('C')]=='C'*s.count('C') for s in seq),
   [s for s in seq if s.count('C') and s[:s.count('C')]!='C'*s.count('C')][:5])
print('== D. 反控 ==')
import random; random.seed(206)
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (0x7fa4b0<=x<0x80efc8)]
rd=random.sample(cands,3000)
ck('D1 区间外 3000 个 8 对齐随机地址满足完整头判据 0 个',
   sum(1 for x in rd if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))==0)
ck('D2 全 .rdata「+0==0 且 +32==self」恰 954 个（非真值 0）',
   sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if P.dw(x)==0 and P.dw(x+32)==x)==954)
ck('D3 段起点判据：块首地址 0x%x 前 4 字节是 .data pTD 指针'%lo, P.where(P.dw(lo-4)) in ('.rdata','.data'))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,lo=hex(lo),hi=hex(hi),region=hi-lo,
  H=cnt['H']*4,C=cnt['C']*24,B=cnt['B']*24,A=cnt['A']*4,P=cnt['P']*4,
  nC=cnt['C'],nB=cnt['B'],nA=cnt['A'],multi=len(multi),badmulti=len(badm),
  single_ok=sum(1 for x in owner if len(refs[x])==1 and owner[x]==refs[x][0]),
  multi_min_ok=sum(1 for x in multi if owner[x]==min(refs[x]))),
  open('_r206/m11_owner2.json','w'),indent=1)
