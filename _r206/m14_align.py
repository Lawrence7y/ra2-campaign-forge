#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m14：RTTI 块对齐规则裁定（m13 唯一 FAIL 的订正）。
证：pad0 不是为了 8 对齐项序列，而是「24B 项序列必须 8 对齐」的下取整；
    pad1 由 pBCA+4n 的模 8 余数决定，但恒 >=4（块尾至少留 4 B）。"""
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
        items=[]
        for j in range((p-q)//24):
            t=q+24*j
            if t in COL and COL[t]['pCHD']==a: items.append((t,'C'))
            elif TDOK(P.dw(t)) and P.dw(t+12)==0xffffffff: items.append((t,'B'))
            else: items=None; break
        if items is not None and [P.dw(p+4*j) for j in range(n)]==BCA[a]:
            blocks[a]=dict(lo=lo,pad0=pad0,items=items,pad1=a-(p+4*n),p=p,n=n); break
print('== A. 项序列 8 对齐 ==')
ck('A1 所有 24B 项地址 8 对齐',all(t%8==0 for b in blocks.values() for t,tp in b['items']),
   sum(1 for b in blocks.values() for t,tp in b['items'] if t%8))
print('== B. pad0 规则 ==')
k=collections.Counter()
for a,b in blocks.items():
    k[(b['pad0'], (b['p']%8), len(b['items'])==0, (b['lo']%8))]+=1
print(' (pad0, pBCA%8, 无项, lo%8) 分布:',k.most_common(8))
ck('B1 lo=prev+36 恒 ≡4 (mod 8)',set(b['lo']%8 for b in blocks.values())=={4})
ck('B2 有 24B 项 ⇒ pad0==4（项序列需 8 对齐）',
   all(b['pad0']==4 for b in blocks.values() if b['items']),
   sum(1 for b in blocks.values() if b['items'] and b['pad0']!=4))
ck('B3 无项且 pBCA≡0(8) ⇒ pad0==0；无项且 pBCA≡4(8) ⇒ pad0==4',
   all((b['pad0']==(0 if b['p']%8==0 else 4)) for b in blocks.values() if not b['items']),
   sum(1 for b in blocks.values() if not b['items'] and b['pad0']!=(0 if b['p']%8==0 else 4)))
print('== C. pad1 规则 ==')
k2=collections.Counter(((b['p']+4*b['n'])%8, b['pad1']) for b in blocks.values())
print(' ((pBCA+4n)%8, pad1):',k2.most_common())
ck('C1 (pBCA+4n)%8==4 ⇒ pad1==4',all(b['pad1']==4 for b in blocks.values() if (b['p']+4*b['n'])%8==4),
   sum(1 for b in blocks.values() if (b['p']+4*b['n'])%8==4 and b['pad1']!=4))
ck('C2 (pBCA+4n)%8==0 ⇒ pad1==8（块尾恒留 >=4 B 填充）',
   all(b['pad1']==8 for b in blocks.values() if (b['p']+4*b['n'])%8==0),
   sum(1 for b in blocks.values() if (b['p']+4*b['n'])%8==0 and b['pad1']!=8))
print('== D. 首条（无前驱块）==')
a0=CHD[0]; p=pBCA[a0]; n=NB[a0]
print(' 首条 head=0x%x pBCA=0x%x n=%d 尾=0x%x pad1=%d'%(a0,p,n,p+4*n,a0-(p+4*n)))
ck('D1 首条 pad1==8 且 (pBCA+4n)%8==0',(a0-(p+4*n))==8 and (p+4*n)%8==0)
print('== E. 块长分布 ==')
L=collections.Counter(b['lo'] and (a-b['lo']) for a,b in blocks.items())
print(' 块长（prev+36..head）top10:',L.most_common(10))
ck('E1 块长恒为 4 的倍数',all((a-b['lo'])%4==0 for a,b in blocks.items()))
ck('E2 块长 >=36',all((a-b['lo'])>=36 for a,b in blocks.items()))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,
  pad0=dict((str(k),v) for k,v in collections.Counter((b['pad0'],len(b['items'])==0) for b in blocks.values()).items()),
  pad1=dict((str(k),v) for k,v in k2.items()),
  blocklen=dict((str(k),v) for k,v in L.most_common(10))),open('_r206/m14_align.json','w'),indent=1)
