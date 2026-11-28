#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m24：复算执行员 #521 的六项数字（§2.12 规则 D，主会话亲跑）。
执行员口径：块 = [prev_head+36, head+36)（含类头 36B 在内）；五类 = HEAD36 / ITEM24 / BCD / BCA / PAD。
本脚本复算其 5 PASS + 1 CONFLICT，并定位其 2412 个「未归属」dword 的构成。"""
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
print('== E1 HEAD 36 字节 ==')
ck('E1.1 954 条 +0==0 且 +32==self',sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+32)==a)==954)
ck('E1.2 位移 -8/-4/+4/+8 后 +32 自指全 0',all(sum(1 for a in CHD if P.dw(a+32+d)==a)==0 for d in (-8,-4,4,8)))
print('== E2 区间 ==')
ck('E2.1 首个类头 0x7fa4c8 / 末个类头 0x80efa0',(CHD[0],CHD[-1])==(0x7fa4c8,0x80efa0),(hex(CHD[0]),hex(CHD[-1])))
ck('E2.2 [首头, 末头+36) = 0x7fa4c8..0x80efc4 = %d B'%(CHD[-1]+36-CHD[0]),(CHD[-1]+36-CHD[0])==84732,CHD[-1]+36-CHD[0])
print('  注：执行员报表「max(HEAD)=0x80eea0」为笔误，其实测高端 dword 列表给出 0x80efa0（=自身）；0x80eea0 是 __non_rtti_object 类头')
print('== E3 记账（执行员口径：块=[prev+36, head+36)）==')
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
# 执行员口径的区间
lo=CHD[0]; hi=CHD[-1]+36
tot=(hi-lo)//4
own={}
def mark(p,t):
    own.setdefault(p,t)
for a in CHD:
    for o in range(a,a+36,4): mark(o,'HEAD36')
for a,b in blocks.items():
    for t,tp in b['items']:
        for o in range(t,t+24,4): mark(o,'ITEM24' if tp=='C' else 'BCD')
    for j in range(b['n']): mark(b['p']+4*j,'BCA')
# 首块的 BCA（在首头之前，执行员区间外）
for j in range(NB[CHD[0]]): mark(pBCA[CHD[0]]+4*j,'BCA')
c=collections.Counter(own.values())
unassigned=[o for o in range(lo,hi,4) if o not in own]
print('  区间 %d dword；已归属 %d；未归属 %d'%((hi-lo)//4,len(own),len(unassigned)))
print('  分类：HEAD36 %d / ITEM24(额外COL) %d / BCD %d / BCA %d'%(c['HEAD36'],c['ITEM24'],c['BCD'],c['BCA']))
print('  执行员报：21183 dword、HEAD36 8586、ITEM24 1560、BCD 6012、BCA 2611、PAD 1、未归属 2412、重复 0')
ck('E3.1 执行员的 8586/1560/6012/2611 全部复现',(c['HEAD36'],c['ITEM24'],c['BCD'],c['BCA'])==(8586,1560,6012,2611),
   (c['HEAD36'],c['ITEM24'],c['BCD'],c['BCA']))
ck('E3.2 其 2412 个未归属 dword == 我模型的 pad（9664 B / 4 = 2416，减去区间外 4 个 dword）',
   len(unassigned)==2412,len(unassigned))
ck('E3.3 未归属 dword 值全 0（是对齐填充，不是缺失子结构）',
   all(P.dw(x)==0 for x in unassigned),collections.Counter(P.dw(x) for x in unassigned).most_common(3))
print('  ⇒ 执行员的 CONFLICT 是口径差异：他把 pad 归为「未归属」，我模型单列 PAD 类；两侧数字互相印证')
print('== E4 归属律 ==')
owner={}
for a,b in blocks.items():
    for t,tp in b['items']:
        if tp=='B': owner[t]=a
refs=collections.defaultdict(list)
for a in CHD:
    for x in BCA[a]: refs[x].append(a)
law=lambda b:(min([y for y in refs[b] if y>b]) if [y for y in refs[b] if y>b] else None)
ck('E4.1 1002/1002 成立',sum(1 for b in owner if owner[b]==law(b))==1002,sum(1 for b in owner if owner[b]==law(b)))
ck('E4.2 反控 max=722',sum(1 for b in owner if owner[b]==max(refs[b]))==722)
ck('E4.3 反控 最近=966',sum(1 for b in owner if owner[b]==min(refs[b],key=lambda y:abs(y-b)))==966)
print('== E5 24B 项形态 ==')
seq=collections.Counter(''.join(tp for t,tp in b['items']) for b in blocks.values())
print(' ',seq.most_common(8))
ck('E5.1 形态分布：空 860 / C 10 / CC 6 / CCC 76 / CCCC 1 / CCCCCC 1（执行员口径）',
   (seq[''],seq['C'],seq['CC'],seq['CCC'],seq['CCCC'],seq['CCCCCC'])==(860,10,6,76,1,1),
   (seq[''],seq['C'],seq['CC'],seq['CCC'],seq['CCCC'],seq['CCCCCC']))
ck('E5.2 C 恒为前缀',all(s[:s.count('C')]=='C'*s.count('C') for s in seq))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,head36=c['HEAD36'],item24=c['ITEM24'],bcd=c['BCD'],bca=c['BCA'],
  unassigned=len(unassigned),seq=dict(seq.most_common())),open('_r206/m24_verify_exec.json','w'),indent=1)
