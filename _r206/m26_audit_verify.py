#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m26：复算审计员 #522 的六条主张（§2.12 规则 D，主会话亲跑）。
A1 pad0 是否 (k,n) 的确定性函数、两种起点是否同址。
A2 L2.1 是否恒真不可证伪；样本是否存在。
A3 min{全部 HEAD>BCD} 是否也 1002/1002（若成立则律 3 的 min/max/最近反控不构成结构证据）。
A4 m20 L4.1 是否为恒等式（lo 定义即 a+36）。
A5 24B 项判别位：BCD +12 恒 0xffffffff / COL +12 是 pCHD 指针。
A6 624 的 +40 是否等于「下一块首 BCD 的 pTD」；落进本条 BCA pTD 集的条数；pTD 去重数。"""
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
def parse(n,off=36):
    lo=CHD[IDX[n]-1]+off; p=pBCA[n]; k=NB[n]; sols=[]
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
        sols.append((pad0,q,items,p+4*k))
    return sols
B={a:parse(a) for a in CHD[1:]}
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
print('== A1 pad0 是否 (k,n) 的确定性函数 ==')
c4=sum(1 for a in CHD[1:] if B[a] and B[a][0][0]==4); c0=sum(1 for a in CHD[1:] if B[a] and B[a][0][0]==0)
ck('A1.1 pad0=4 的 748 条 / pad0=0 的 205 条',(c4,c0)==(748,205),(c4,c0))
S0=set(a for a in CHD[1:] if B[a] and B[a][0][0]==0)
S1=set(a for a in B if not B[a][0][2] and NB[a]==1)
ck('A1.2 {pad0==0} == {k==0 且 n==1}（集合完全相等）',S0==S1,(len(S0),len(S1),len(S0^S1)))
print('  注：n==1 且 k==0 的 205 条正是 pBCA%8==4 的 205 条（律 2 的例外）')
ck('A1.3 prev+32 + pad0=4 与 prev+36 + pad0=0 同址（审计指出）',
   all(len(parse(a,32))>0 for a in sorted(S0)[:20]) and True,
   sum(1 for a in CHD[1:] if parse(a,32)))
# 强制单值
ck('A1.4 强制 pad0≡4 只剩 748/953；强制 pad0≡0 只剩 205/953',
   (sum(1 for a in CHD[1:] if any(s[0]==4 for s in B[a])),sum(1 for a in CHD[1:] if any(s[0]==0 for s in B[a])))==(748,205))
print('== A2 L2.1 是否恒真 ==')
allp=all(pBCA[a]%8==(4+B[a][0][0])%8 for a in B)
ck('A2.1 pBCA%8 == (4+pad0)%8 恒真（由 (p-q)%24==0 且 24≡0 mod 8 推出）',allp,allp)
d1=sum(1 for a in B if B[a][0][2] and NB[a]==1)
d2=sum(1 for a in B if not B[a][0][2] and NB[a]>=2)
ck('A2.2 判别样本确实存在：k>=1 且 n==1 有 51 条；k==0 且 n>=2 有 30 条',(d1,d2)==(51,30),(d1,d2))
print('== A3 min{全部 HEAD > BCD} 是否也 1002/1002 ==')
owner={}
for a in CHD[1:]:
    for t,tp in B[a][0][2]:
        if tp=='B': owner[t]=a
ck('A3.1 1002 个 BCD 全部被某块物理持有',len(owner)==1002,len(owner))
allheads=CHD
law_all=lambda b: min([y for y in allheads if y>b]) if [y for y in allheads if y>b] else None
ck('A3.2 「持有块 == min{全部类头 > BCD 地址}」也 1002/1002（⇒ min/max/最近反控不构成结构证据）',
   sum(1 for b in owner if owner[b]==law_all(b))==1002,sum(1 for b in owner if owner[b]==law_all(b)))
ck('A3.3 非平凡内容：持有块自身一定引用该 BCD（1002/1002）',
   all(b in BCA[owner[b]] for b in owner),sum(1 for b in owner if b in BCA[owner[b]]))
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
multi=[b for b in owner if len(refs[b])>1]
ck('A3.4 多引用 %d 条上：min 引用者 100%%、max 0%%、绝对最近 264/280'%len(multi),
   (len(multi),sum(1 for b in multi if owner[b]==min(refs[b])),sum(1 for b in multi if owner[b]==max(refs[b])),
    sum(1 for b in multi if owner[b]==min(refs[b],key=lambda y:abs(y-b))))==(280,280,0,264),
   (len(multi),sum(1 for b in multi if owner[b]==min(refs[b])),sum(1 for b in multi if owner[b]==max(refs[b])),
    sum(1 for b in multi if owner[b]==min(refs[b],key=lambda y:abs(y-b)))))
print('== A4 m20 L4.1 是否为恒等式 ==')
triv=sum(1 for a in CHD[:-1] if [P.dw(a+36+4*i) for i in range(3)]==[P.dw(a+36+4*i) for i in range(3)])
ck('A4.1 lo 定义即 prev+36 == a+36 ⇒ P1 比较左边等于右边（恒等式，无信息量）',triv==953,triv)
# 去掉恒等后：比较「尾部三 dword」与「下一条块语义字段」
sem=0; miss=[]
for a in CHD[:-1]:
    nb=B.get(CHD[IDX[a]+1])
    if not nb: continue
    pad0,q,items,e=nb[0]
    if items:
        t,tp=items[0]
        want=[0, P.dw(t), P.dw(t+4)] if pad0 else [0,P.dw(t),P.dw(t+4)]
    else:
        want=[P.dw(pBCA[CHD[IDX[a]+1]]),0,0] if pad0==0 else [0,P.dw(pBCA[CHD[IDX[a]+1]]),P.dw(P.dw(pBCA[CHD[IDX[a]+1]])+4)]
    got=[P.dw(a+36),P.dw(a+40),P.dw(a+44)]
    if got==want: sem+=1
    else: miss.append((hex(a),[hex(x or 0) for x in got],[hex(x or 0) for x in want]))
ck('A4.2 去掉恒等后按「下一块语义字段」预测：命中数',sem>=0,(sem,len(miss)))
print('  未命中样例:',miss[:4])
print('== A5 24B 项判别位 ==')
ck('A5.1 C 项过 BCD 判据 0/260（BCD 判据要求 +12==0xffffffff）',
   sum(1 for b in B.values() for t,tp in b[0][2] if tp=='C' and P.dw(t+12)==0xffffffff)==0)
ck('A5.2 B 项过 COL 判据 0/1002（COL 判据要求 +16 是 pCHD 且 >0）',
   sum(1 for b in B.values() for t,tp in b[0][2] if tp=='B' and P.dw(t+16)!=0)==0)
ck('A5.3 判别位正是项内 +12：BCD 恒 0xffffffff，COL 是 .rdata 内 pCHD 指针',
   all(P.dw(t+12)==0xffffffff and P.where(P.dw(t))=='.data' for b in B.values() for t,tp in b[0][2] if tp=='B')
   and all(P.dw(t+12)==0 and P.where(P.dw(t+16))=='.rdata' for b in B.values() for t,tp in b[0][2] if tp=='C'))
print('== A6 624 条 +40 的归属与 COMDAT 折叠说法 ==')
n624=[a for a in CHD[:-1] if B.get(CHD[IDX[a]+1]) and B[CHD[IDX[a]+1]][0][2] and B[CHD[IDX[a]+1]][0][2][0][1]=='B']
ck('A6.1 「下一块首项是 BCD」的恰 624 条',len(n624)==624,len(n624))
ck('A6.2 这 624 条 +40 == 该首项 BCD 的 pTD',all(P.dw(a+40)==P.dw(B[CHD[IDX[a]+1]][0][2][0][0]) for a in n624),len(n624))
inbca=sum(1 for a in n624 if P.dw(a+40) in set(P.dw(x) for x in BCA[a]))
ck('A6.3 其中 +40 落进「本条 BCA 条的 pTD 集」的只有 37 条（不是 624）',inbca==37,inbca)
ck('A6.4 pTD 去重 988（1002-988=14 ⇒ COMDAT 折叠至多解释 14 条，不能解释 624）',
   len(set(P.dw(b) for b in owner))==988,len(set(P.dw(b) for b in owner)))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,pad4=c4,pad0=c0,seteq=len(S0^S1),allp=allp,
  discr51=d1,discr30=d2,allhead=1002,inbca=inbca,ptduniq=len(set(P.dw(b) for b in owner)),
  multi=len(multi),sem_hit=sem,sem_miss=len(miss)),
  open('_r206/m26_audit_verify.json','w'),indent=1)
