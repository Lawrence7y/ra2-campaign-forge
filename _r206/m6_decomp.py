#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m6：逐记录块分解 —— [pad][BCD*k][BCA*n][pad][CHD 36B]，并解释 L=48 特例与长 gap 段。
正控：+32==self 954/954。反控：块基址整体位移后分解失败率应升。"""
import sys,struct,collections
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
PREV={a:(CHD[i-1] if i>0 else None) for i,a in enumerate(CHD)}
N={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(N[a])] for a in CHD}
ptd={a:P.dw(a+28) for a in CHD}
print('== A. 逐记录：从 prev+36 到 a，识别 [BCD...][BCA][pad] ==')
stat=collections.Counter(); bad=[]
for i,a in enumerate(CHD):
    lo = (PREV[a]+36) if PREV[a] else None
    if lo is None:
        stat['first']+=1; continue
    ent=BCA[a]; p=pBCA[a]; nb=N[a]
    # BCD 区: 从 lo 起 8 对齐后的位置到 p
    q=lo+((8-lo%8)%8) if lo%8 else lo
    # 该区应全部是 24 字节 BCD
    nbc=(p-q)//24 if p>=q else -1
    ok24 = (p-q)%24==0 and p>=q
    # 校验每个 24 槽是否为合法 BCD 形状
    okbcd=True
    for k in range(max(nbc,0)):
        b=q+24*k; td=P.dw(b); nc=P.dw(b+4); md=s32(P.dw(b+8)); pd=s32(P.dw(b+12))
        if P.where(td)!='.data' or nc is None or nc>30 or pd!=-1: okbcd=False; break
    # BCA 之后到 a 的 padding
    tail=a-(p+4*nb)
    stat[(a-lo, q-lo, ok24, okbcd, tail, nbc, nb)]+=1
    if not (ok24 and okbcd and tail in (0,4,8) and set(ent)<=set(q+24*k for k in range(max(nbc,0)))):
        bad.append((a,hex(a),a-lo,q-lo,ok24,okbcd,tail,nbc,nb,[hex(x) for x in ent]))
print(' 组合计数 top14:')
for k,v in stat.most_common(14): print('   Lg=%s pad0=%s mod24=%s bcdshape=%s tail=%s nBCD=%s nBCA=%s : %d'%(k[0],k[1],k[2],k[3],k[4],k[5],k[6],v))
print(' 不满足模型的记录数 %d'%len(bad))
for x in bad[:8]: print('   ',x)
print('== B. L=48 的 205 条特例：区间长度 12，内容是什么 ==')
sp=[a for a in CHD if PREV[a] and a-PREV[a]==48]
print(' count',len(sp))
kk=collections.Counter()
for a in sp:
    kk[tuple(hex(P.dw(a+o) or 0) for o in (36,40,44))]+=1
print(' (+36,+40,+44) 形态 top5:')
for k,v in kk.most_common(5): print('   ',k,v)
print(' +36 目标类型:',collections.Counter(('BCD' if P.dw(a+36) in set(b for x in CHD for b in BCA[x]) else ('COL' if P.dw(a+36) in COL else P.where(P.dw(a+36)))) for a in sp).most_common())
print(' +40 目标类型:',collections.Counter(P.where(P.dw(a+40)) if P.dw(a+40) else 'zero' for a in sp).most_common())
print(' +36 目标==本记录某 BCD?',sum(1 for a in sp if P.dw(a+36) in BCA[a]))
print(' +36 目标==自身 pTD 的 BCD?',sum(1 for a in sp if P.dw(a+36) in BCA[a] and P.dw(P.dw(a+36))==ptd[a]))
print(' +40 目标 in ptdset:',sum(1 for a in sp if P.dw(a+40) in set(ptd.values())))
print(' +36 目标 相对自身:',collections.Counter(P.dw(a+36)-a for a in sp).most_common(6))
print('== C. 19-dword gap 段（76 个）是什么 ==')
own={}
for a in CHD:
    for o in range(a,a+36,4): own[o]='H'
    for j in range(N[a]): own[pBCA[a]+4*j]='A'
for b in set(b for x in CHD for b in BCA[x]):
    for o in range(b,b+24,4): own[o]='B'
gap=[o for o in range(min(own),max(own)+4,4) if o not in own]
runs=[]
for o in gap:
    if runs and o==runs[-1][1]+4: runs[-1][1]=o
    else: runs.append([o,o])
r19=[(a,b) for a,b in runs if (b-a)//4+1==19]
print(' 段数 %d，首 4 段 dump:'%len(r19))
for a,b in r19[:3]:
    print('  0x%x..0x%x'%(a,b),[hex(P.dw(o) or 0) for o in range(a,b+4,4)])
    # 前后 CHD
    pv=[x for x in CHD if x<a][-1]; nx=[x for x in CHD if x>b]
    print('    prev CHD 0x%x (%s) next CHD 0x%x'%(pv,COL[G[pv][0]]['name'][:30],nx[0] if nx else 0))
print('== D. 记账终值 ==')
tot=(max(own)+4-min(own))
print(' 区间 %d B：CHD/COL %d B、BCA %d B、BCD %d B、gap %d B'%(tot,
   sum(1 for o in own if own[o]=='H')*4,sum(1 for o in own if own[o]=='A')*4,
   sum(1 for o in own if own[o]=='B')*4,len(gap)*4))
print(' 理论：954*36=%d  2615*4=%d  1002*24=%d  和=%d'%(954*36,2615*4,1002*24,954*36+2615*4+1002*24))
