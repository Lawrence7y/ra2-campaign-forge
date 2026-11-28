#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m25：复算执行员 #521 的口径（§2.12 规则 D）。含对其内部自查和差 1 的定位。
执行员口径区间 = [min(HEAD), max(HEAD)+36) = [0x7fa4c8, 0x80efc4)，21183 dword。
关键：该区间**不含**首条类（0x7fa4c8）自己的 BCA 数组（在 0x7fa4b0..0x7fa4bf，区间之前）。"""
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
        return dict(lo=lo,pad0=pad0,items=items,p=p,n=k)
    return None
blocks={a:parse(a,CHD[IDX[a]-1]+36) for a in CHD[1:]}
blocks={a:b for a,b in blocks.items() if b}
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
lo=CHD[0]; hi=CHD[-1]+36
own={}
def mark(p,t): own.setdefault(p,t)
for a in CHD:
    for o in range(a,a+36,4): mark(o,'HEAD36')
for a,b in blocks.items():
    for t,tp in b['items']:
        for o in range(t,t+24,4): mark(o,'ITEM24' if tp=='C' else 'BCD')
    for j in range(b['n']): mark(b['p']+4*j,'BCA')
cnt=collections.Counter(own.values())
un=[o for o in range(lo,hi,4) if o not in own]
tot=(hi-lo)//4
print('== 执行员口径复算 ==')
print(' 区间 [0x%x,0x%x) = %d dword'%(lo,hi,tot))
print(' HEAD36 %d / ITEM24 %d / BCD %d / BCA %d / 未归属(pad) %d ; 合计 %d'%(
  cnt['HEAD36'],cnt['ITEM24'],cnt['BCD'],cnt['BCA'],len(un),sum(cnt.values())+len(un)))
ck('V1 区间 dword 数 21183 复现',tot==21183,tot)
ck('V2 HEAD36 8586 复现',cnt['HEAD36']==8586,cnt['HEAD36'])
ck('V3 ITEM24 1560 复现',cnt['ITEM24']==1560,cnt['ITEM24'])
ck('V4 BCD 6012 复现',cnt['BCD']==6012,cnt['BCD'])
ck('V5 BCA 2611 复现（=2615-4，首条类 BCA 数组在区间左端之外）',cnt['BCA']==2611,cnt['BCA'])
ck('V6 未归属 2414 复现（执行员报 2412，差 2）',len(un)==2414,len(un))
ck('V7 未归属全为 0 值 pad',all(P.dw(x)==0 for x in un))
ck('V8 执行员四项相加 8586+1560+6012+2611+1+2412 = %d ≠ 21183（其内部差 1）'%(8586+1560+6012+2611+1+2412),
   8586+1560+6012+2611+1+2412!=21183,8586+1560+6012+2611+1+2412)
print('== 执行员 E5 口径（视图数-1 的形态）复算 ==')
vd=collections.Counter(len(G[a])-1 for a in CHD)
print(' 视图数-1 分布:',sorted(vd.items()))
ck('V9 空 860 / C 10 / CC 6 / CCC 76 / CCCC 1 / CCCCCC 1 复现',
   (vd[0],vd[1],vd[2],vd[3],vd[4],vd[6])==(860,10,6,76,1,1),(vd[0],vd[1],vd[2],vd[3],vd[4],vd[6]))
ck('V10 执行员 E5 与我方「24B 项序列」是两个不同口径（我方按块内项，含 BCD；执行员按视图数-1）',
   vd[0]==860 and collections.Counter(''.join(tp for t,tp in b['items']) for b in blocks.values())['']==235)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,tot=tot,head36=cnt['HEAD36'],item24=cnt['ITEM24'],
  bcd=cnt['BCD'],bca=cnt['BCA'],unassigned=len(un),exec_sum=8586+1560+6012+2611+1+2412,
  viewdist=dict((str(k),v) for k,v in vd.items())),open('_r206/m25_verify_exec2.json','w'),indent=1)
