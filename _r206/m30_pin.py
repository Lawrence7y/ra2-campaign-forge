#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m30：钉死 m29 余下两条的实测值（不预设结论）。
1.3 口径：a+36..+47 中与本条 pTD 相等的值，逐条核对是否等于「下一条块首 BCD 的 pTD」（别名而非本条字段）。
5.2 口径：修正 pad0=4 无项块的 +44 公式后重算语义预测命中数。"""
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
print('== 1.3 别名核查 ==')
hits=[]
for a in CHD[:-1]:
    for i in range(3):
        v=P.dw(a+36+4*i)
        if v in (a,a+16,pBCA[a]): hits.append((hex(a),i,'self-field',hex(v)))
        if v==P.dw(a+28): hits.append((hex(a),i,'own-pTD',hex(v)))
print(' 命中总数 %d'%len(hits))
print(' 分类:',collections.Counter(h[2] for h in hits).most_common())
print(' 样例:',hits[:4])
# 这 26 条 own-pTD 命中：值 == 下一条块首 BCD 的 pTD 吗
own=[h for h in hits if h[2]=='own-pTD']
aliased=0
for h in own:
    a=int(h[0],16); b=B.get(CHD[IDX[a]+1])
    if b and b[2] and b[2][0][1]=='B' and P.dw(a+40)==P.dw(b[2][0][0]): aliased+=1
ck('1.3a 命中集合只含「本条 own-pTD」一类（无 self/+16/pBCA 命中）',
   set(h[2] for h in hits)=={'own-pTD'},set(h[2] for h in hits))
ck('1.3b 这 %d 条全部是别名：值 == 下一条块首 BCD 的 pTD（不是本条字段）'%len(own),aliased==len(own),(aliased,len(own)))
ck('1.3c 且这 %d 条的 +40 位置固定（i==1）'%len(own),all(h[1]==1 for h in own),collections.Counter(h[1] for h in own).most_common())
print('== 5.2 语义预测（修正 30 条公式后）==')
sem=0; miss=[]
for a in CHD[:-1]:
    b=B.get(CHD[IDX[a]+1])
    if not b: continue
    pad0,q,items,e=b
    if items:
        t,tp=items[0]
        want=[0,P.dw(t),P.dw(t+4)]
    else:
        p=pBCA[CHD[IDX[a]+1]]
        want=[P.dw(p),0,0] if pad0==0 else [0,P.dw(p),P.dw(p+4)]
    if [P.dw(a+36),P.dw(a+40),P.dw(a+44)]==want: sem+=1
    else: miss.append(hex(a))
ck('5.2a 953 条全部可由下一条块解析预测',sem==953,(sem,len(miss)))
print(' 未命中:',miss[:5])
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,hits=len(hits),own_hits=len(own),aliased=aliased,sem=sem,miss=len(miss)),
  open('_r206/m30_pin.json','w'),indent=1)
