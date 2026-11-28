#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m13（定稿）：gamemd.exe 类 RTTI 物理块的完全字节记账 + 三条结构律。
模型（全部 954/954 逐条成立）：
  类记录头 HEAD = 36 B：+0=0 / +4=attributes / +8=numBaseClasses / +12=pBCA / +16..+35=内嵌主对象 COL(20 B, pCHD==HEAD)
  类块（从 prev_HEAD+36 到本 HEAD）=  [pad0 0/4 B][24 B 项序列][BCA 4*n B][pad1 4/8 B][HEAD 36 B]
  24 B 项 = 额外视图 COL（pCHD==本 HEAD，C）或 BCD（B）；C 恒为前缀。
  归属律：每条 BCD 物理落在 min{引用它的类 HEAD : HEAD > BCD 地址} 的块里（1002/1002）。
正控：954 自指 +32；反控：区间外随机 8 对齐地址 0 命中、律换成 max/最近均 <100%。"""
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
# 记账（按字节）
own={}; dup=[]
def mark(p,t,who):
    for o in range(p,p+4,4):
        if o in own: dup.append((hex(o),own[o],who,t))
        else: own[o]=(who,t)
def marklen(p,ln,t,who):
    for o in range(p,p+ln,4): mark(o,t,who)
for a in CHD: marklen(a,36,'H',a)
a0=CHD[0]
marklen(pBCA[a0],4*NB[a0],'A',a0)
# 首条的 pad1（0x7fa4c0..0x7fa4c7）
marklen(pBCA[a0]+4*NB[a0],a0-(pBCA[a0]+4*NB[a0]),'P',a0)
for a,b in blocks.items():
    if b['pad0']: marklen(b['lo'],4,'P',a)
    for t,tp in b['items']: marklen(t,24,tp,a)
    marklen(b['p'],4*b['n'],'A',a)
    q=b['p']+4*b['n']
    marklen(q,a-q,'P',a)
cnt=collections.Counter(v[1] for v in own.values())
lo=min(own); hi=max(own)+4
ck('A1 无重叠归属',len(dup)==0,dup[:3])
ck('A2 无空洞（区间内每个 dword 都归属）',len([o for o in range(lo,hi,4) if o not in own])==0)
ck('A3 区间 [0x%x,0x%x) = %d B == 记账总和'%(lo,hi,hi-lo),
   hi-lo==sum(cnt.values())*4,(hi-lo,sum(cnt.values())*4))
print('  记账：H 头36B×954=%d / C 额外COL 24B×260=%d / B BCD 24B×1002=%d / A BCA 4B×2615=%d / P pad 4B×%d=%d'%(
  cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4,cnt['P'],cnt['P']*4))
ck('A4 计数：H 34344 / C 6240 / B 24048 / A 10460 / P 逐字节',
   (cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4)==(34344,6240,24048,10460),(cnt['H']*4,cnt['C']*4,cnt['B']*4,cnt['A']*4))
ck('A5 pad dword 全 0',all(P.dw(p)==0 for p,v in own.items() if v[1]=='P'))
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
ck('B1 持有块 == min{引用者 HEAD : HEAD > BCD 地址} 1002/1002',
   sum(1 for b in owner if owner[b]==law(b))==1002,sum(1 for b in owner if owner[b]==law(b)))
ck('B2 反控 max 引用者',sum(1 for b in owner if owner[b]==max(refs[b]))==722,
   sum(1 for b in owner if owner[b]==max(refs[b])))
ck('B3 反控 最近引用者',sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b)))==966,
   sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b))))
ck('B4 单引用 BCD 698 条：持有者==唯一引用者',sum(1 for b in owner if len(refs[b])==1 and owner[b]==refs[b][0])==698,
   (sum(1 for b in owner if len(refs[b])==1),sum(1 for b in owner if len(refs[b])==1 and owner[b]==refs[b][0])))
print('== C. 24B 项序列 ==')
seq=collections.Counter(''.join(tp for t,tp in b['items']) for b in blocks.values())
print('  形态 top12:',seq.most_common(12))
ck('C1 只含 C/B',all(set(s)<={'C','B'} for s in seq))
ck('C2 C 恒为前缀',all(s[:s.count('C')]=='C'*s.count('C') for s in seq))
ck('C3 有 C 的块 94 个（=多视图类）、无 C 的 859 个',(sum(v for s,v in seq.items() if 'C' in s),sum(v for s,v in seq.items() if 'C' not in s))==(94,859),
   (sum(v for s,v in seq.items() if 'C' in s),sum(v for s,v in seq.items() if 'C' not in s)))
ck('C4 C 项总数 260 == 1214-954',sum(s.count('C')*v for s,v in seq.items())==260,sum(s.count('C')*v for s,v in seq.items()))
ck('C5 每块 C 数 == 该类视图数-1',
   all(sum(1 for t,tp in b['items'] if tp=='C')==len(G[a])-1 for a,b in blocks.items()),
   collections.Counter(sum(1 for t,tp in b['items'] if tp=='C')-len(G[a])+1 for a,b in blocks.items()).most_common(4))
print('== D. pad 结构 ==')
print('  (pad0,pad1) 分布:',collections.Counter((b['pad0'],b['pad1']) for b in blocks.values()).most_common())
ck('D1 pad0 ∈{0,4}，pad1∈{4,8}',all(b['pad0'] in (0,4) and b['pad1'] in (4,8) for b in blocks.values()))
ck('D2 pad0==0 ⟺ prev_HEAD+36 已 8 对齐',all((b['pad0']==0)==((b['lo']%8)==0) for b in blocks.values()))
print('== E. 反控 ==')
random.seed(206)
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (lo<=x<hi)]
ck('E1 区间外 3000 个 8 对齐随机地址满足完整头判据 0 个',
   sum(1 for x in random.sample(cands,3000) if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))==0)
ck('E2 全 .rdata「+0==0 且 +32==self」恰 954',sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if P.dw(x)==0 and P.dw(x+32)==x)==954)
ck('E3 头集整体 +4 位移后自指 0 命中',sum(1 for a in CHD if P.dw(a+36)==a)==0)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,lo=hex(lo),hi=hex(hi),region=hi-lo,
  H=cnt['H']*4,C=cnt['C']*4,B=cnt['B']*4,A=cnt['A']*4,P=cnt['P']*4,
  nC=260,nB=1002,nA=2615,law_ok=1002,law_max=722,law_near=966,
  seq=dict(seq.most_common(12)),pad=dict((str(k),v) for k,v in collections.Counter((b['pad0'],b['pad1']) for b in blocks.values()).items())),
  open('_r206/m13_final.json','w'),indent=1)
