#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m22：把 +40 的语义钉成「下一条类块首个自有 BCD 的 pTD」，并验证 = 基类链。
附加发现候选：「+40 == 本条 pTD」⟺「下一条类在本条 BCA 中被引为基类」。"""
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
blocks={a:parse(a,CHD[IDX[a]-1]+36) for a in CHD[1:]}
blocks={a:b for a,b in blocks.items() if b}
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
nn=[a for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1])]
hasB=[a for a in nn if blocks[CHD[IDX[a]+1]]['items'] and blocks[CHD[IDX[a]+1]]['items'][0][1]=='B']
print('== A. +40 == 下一条块首个 BCD 的 pTD ==')
ck('A1 624 条（下一条块首项为 BCD）全部成立',all(P.dw(a+40)==P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]) for a in hasB),len(hasB))
own_eq=[a for a in hasB if P.dw(a+40)==P.dw(a+28)]
print('  其中 +40 == 本条 pTD 的：%d 条'%len(own_eq))
print('  这 %d 条：'%len(own_eq),[(hex(a),COL[G[a][0]]['name'][:34],'->',COL[G[CHD[IDX[a]+1]][0]]['name'][:34]) for a in own_eq[:6]])
print('== B. 基类链判据：下一条类是否把本条 pTD 放进自己的 BCA ==')
ownptd={a:P.dw(a+28) for a in CHD}
def next_has_own(a):
    nx=CHD[IDX[a]+1]
    return ownptd[a] in [P.dw(b) for b in BCA[nx]]
h1=sum(1 for a in hasB if next_has_own(a))
h2=sum(1 for a in hasB if next_has_own(a) and P.dw(a+40)==ownptd[a])
print('  624 条中「下一条 BCA 含本条 pTD」的 %d 条；其中 +40==本条pTD 的 %d 条'%(h1,h2))
ck('B1 抽样：+40==本条 pTD 的 %d 条全部满足「下一条 BCA 含本条 pTD」'%len(own_eq),
   all(next_has_own(a) for a in own_eq),len(own_eq))
# 反例：下一条含本条 pTD 但 +40 != 本条 pTD
oth=[a for a in hasB if next_has_own(a) and P.dw(a+40)!=ownptd[a]]
print('  反例（下一条有本条 pTD 但 +40 不是本条 pTD）：%d 条'%len(oth),
      [(hex(a),COL[G[a][0]]['name'][:26],COL[G[CHD[IDX[a]+1]][0]]['name'][:26]) for a in oth[:5]])
ck('B2 +40 判据不是基类链判据：%d 条反例'%len(oth),len(oth)>0,len(oth))
print('  ⇒ 结论：+40 是「下一条块首个 BCD 的 pTD」= 该类 RTTI 块首基类记录，不是基类链本身')
print('== C. +44 == 该 BCD 的 numContained（非 0 的 26 条）==')
nz=[a for a in hasB if P.dw(a+44)]
print('  非零 %d 条，值分布 %s'%(len(nz),collections.Counter(P.dw(a+44) for a in nz).most_common(6)))
ck('C1 非零时恒等于该 BCD 的 numContained',all(P.dw(a+44)==P.dw(blocks[CHD[IDX[a]+1]]['items'][0][0]+4) for a in nz),len(nz))
print('== D. 30 条「pad0=4 且无项」块的 +44 ==')
s30=[a for a in CHD[:-1] if blocks.get(CHD[IDX[a]+1]) and not blocks[CHD[IDX[a]+1]]['items'] and blocks[CHD[IDX[a]+1]]['pad0']==4]
print('  %d 条，+36/+40/+44 ='%len(s30),collections.Counter((P.dw(a+36),P.dw(a+44)) for a in s30).most_common(5))
ck('D1 这 30 条的 +36==0 且 +44==下一条 BCA[1] 指向的 BCD.mdisp',
   all(P.dw(a+36)==0 and P.dw(a+44)==s32(P.dw(blocks[CHD[IDX[a]+1]]['p']+4)+4) for a in s30),len(s30))
print('  （即 +40 是下一条 BCA[0]、+44 是 BCA[1] 所指 BCD 的 mdisp —— 说明 pad0=4 处 4 字节为 0）')
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,hasB=len(hasB),own_eq=len(own_eq),next_has_own=h1,other=len(oth),nz=len(nz),s30=len(s30)),
  open('_r206/m22_baselink.json','w'),indent=1)
