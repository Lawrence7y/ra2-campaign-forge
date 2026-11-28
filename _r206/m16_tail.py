#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m16：+36/+40/+44 三字段「属于下一条类块」的判定（R205 未取得项①）。
证：每条记录 a 的 +36/+40/+44 全部由**下一条类块的 24B 项序列**决定，不含本条任何字段。
正控：尾部字节可 100% 反解出 next 的 pad0/首项类型；反控：把 next 换成本条自身则全崩。"""
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
def firstitem(a):
    """返回 next 块的首项 (addr,kind,pad0)"""
    i=IDX[a]; 
    if i+1>=len(CHD): return None
    n=CHD[i+1]; lo=a+36; p=pBCA[n]
    for pad0 in (0,4):
        q=lo+pad0
        if q>p or (p-q)%24: continue
        if q==p: return (None,'none',pad0,q)  # 无 24B 项，q 即 pBCA
        if q in COL and COL[q]['pCHD']==n: return (q,'C',pad0,q)
        if TDOK(P.dw(q)) and P.dw(q+12)==0xffffffff: return (q,'B',pad0,q)
    return None
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
print('== A. 尾部字节归属表 ==')
k=collections.Counter()
for a in CHD[:-1]:
    fi=firstitem(a)
    if fi is None: k['parse-fail']+=1; continue
    f=fi[1]
    k[(f, P.dw(a+36), P.dw(a+40), P.dw(a+44))]+=1
for kk,v in k.most_common(12):
    print('  首项=%-4s +36=%-10s +40=%-10s +44=%-6s : %d'%(kk[0],hex(kk[1] or 0),hex(kk[2] or 0),hex(kk[3] or 0),v))
ck('A1 953 条尾部全部可解析（无 parse-fail）',k['parse-fail']==0,k['parse-fail'])
# 逐条验证：首项==B ⇒ +40==BCD.pTD(.data)；首项==C ⇒ +40==COL.sig==0；无项 ⇒ +36==pBCA(next)
okB=okC=okN=0; tB=tC=tN=0
for a in CHD[:-1]:
    fi=firstitem(a); f=fi[1]
    if f=='B':
        tB+=1; okB+= (P.dw(a+40)==P.dw(fi[0]) and P.where(P.dw(a+40))=='.data')
    elif f=='C':
        tC+=1; okC+= (P.dw(a+40)==0)
    elif f=='none':
        tN+=1; okN+= (P.dw(a+36)==pBCA[CHD[IDX[a]+1]])
ck('A2 首项 BCD 的块：下一条 +40 == 该 BCD 的 pTD（.data）',okB==tB,(okB,tB))
ck('A3 首项额外COL 的块：下一条 +40 == COL.sig == 0',okC==tC,(okC,tC))
ck('A4 无 24B 项的块：下一条 +36 == pBCA',okN==tN,(okN,tN))
ck('A5 三条合计 953',(tB,tC,tN) and tB+tC+tN==953,(tB,tC,tN))
print('== B. 反控：把尾部按"本条字段"解释 ==')
ck('B1 无一条 +36..+47 指向本条自身或本条 BCD/COL',all(
   v not in (a,a+16) and v not in BCA[a] for a in CHD[:-1] for v in (P.dw(a+36),P.dw(a+40),P.dw(a+44)) if v),
   'ok')
# +44 的三种值：BCD.numContained / COL.mdisp / pBCA 低位
kk=collections.Counter()
for a in CHD[:-1]:
    fi=firstitem(a); v=P.dw(a+44)
    if fi[1]=='B': kk[('B',v==P.dw(fi[0]+4))]+=1
    elif fi[1]=='C': kk[('C',v==P.dw(fi[0]+4))]+=1
    else: kk[('N',v==0)]+=1
print('  +44 语义核对 (首项类型, +44==首项+4):',kk.most_common())
ck('B2 +44 == 首项的第二个 dword（BCD.numContained 或 COL.mdisp）；无项时为 0',
   sum(v for kk2,v in kk.items() if kk2[1])==953,kk.most_common())
print('== C. 结论向量 ==')
print(' 首项类型分布 B/C/none = %d/%d/%d'%(tB,tC,tN))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,kindB=tB,kindC=tC,kindNone=tN,
   okB=okB,okC=okC,okNone=okN,tail=k and dict((str(x[0])+':'+hex(x[1] or 0),v) for x,v in k.most_common(8))),
   open('_r206/m16_tail.json','w'),indent=1)
