#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m4：RTTI 块物理布局模型 —— [BCD*][BCA*][36B CHD]。
关键假设：CHD 头是 36 字节（不是 40/48）；prev+36 起是**下一条记录**的 BCD 数组，
其后是本条 BCA 数组，再后是本条 36B 头。
正控：954 条 pBCA 全 .rdata、BCA 条目全落 [prev+36, pBCA]；反控：把起点位移 ±4/±8/±12/±24 后命中应塌。"""
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
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

print('== A. 线性原始 dump：0x7fa440..0x7fa5a0（每 dword，附分类）==')
ptdset=set(P.dw(a+28) for a in CHD)
def tag(v):
    if v is None: return 'none'
    if v in COL: return 'COL@%x(%s)'%(v,COL[v]['name'][:22])
    if v in ptdset: return 'TD'
    if v==0xffffffff: return '-1'
    if v==0: return '0'
    w=P.where(v)
    return w or 'other'
for off in range(0x7fa440,0x7fa5a0,4):
    v=P.dw(off)
    extra=''
    if off in CHD: extra=' <<< CHD '+COL[G[off][0]]['name'][:34]
    elif any(off==P.dw(a+12) for a in CHD if P.dw(a+12)==off): extra=' <<< pBCA'
    print('  0x%x %08x %s%s'%(off,v,tag(v),extra))
print('== B. 结构测试：CHD 头 = 36 字节，前驱区间属于本条 ==')
lst=[]
for a in CHD:
    pv=PREV[a]
    if pv is None: continue
    p=P.dw(a+12); n=P.dw(a+8); ent=BCA[a]
    lo=pv+36
    lst.append((a,lo,p,ent,n))
ck('B1 pBCA 落在 (prev+36, a) 内 953/953',all(lo<p<a for a,lo,p,ent,n in lst),sum(1 for a,lo,p,e,n in lst if lo<p<a))
ck('B2 pBCA-(prev+36) 恒为 24 的倍数',all((p-lo)%24==0 for a,lo,p,e,n in lst),
   collections.Counter((p-lo)%24 for a,lo,p,e,n in lst))
ck('B3 所有 BCA 条目落 [prev+36, pBCA+4n]',all(all(lo<=b<p+4*n for b in ent) for a,lo,p,ent,n in lst),
   sum(1 for a,lo,p,ent,n in lst if not all(lo<=b<p+4*n for b in ent)))
ck('B4 BCA 数组尾 <= a（数组在头之前）',all(p+4*n<=a for a,lo,p,e,n in lst),sum(1 for a,lo,p,e,n in lst if p+4*n>a))
print('  (pBCA+4n) 到 a 的填充字节分布:',collections.Counter(a-(p+4*n) for a,lo,p,e,n in lst).most_common(8))
print('  pBCA-(prev+36) 分布:',collections.Counter(p-lo for a,lo,p,e,n in lst).most_common(8))
print('== C. 每条记录的 BCD 槽数 vs 被引用 BCD 数 ==')
k=collections.Counter(); miss=0; extra=0
for a,lo,p,ent,n in lst:
    slots=set(lo+24*i for i in range((p-lo)//24))
    ref=set(ent)
    k[(len(slots),len(ref),len(slots-ref))]+=1
    miss+=len(slots-ref); extra+=len(ref-slots)
ck('C1 全部 BCA 条目地址 == 槽基址（24 对齐于 prev+36）',
   all(all((b-lo)%24==0 for b in ent) for a,lo,p,ent,n in lst),
   sum(1 for a,lo,p,ent,n in lst if not all((b-lo)%24==0 for b in ent)))
print('  槽数-引用数-未引用 计数 top10:',k.most_common(10))
print('  未引用槽总数 %d；引用不在槽内的 BCD 数 %d'%(miss,extra))
print('== D. 反控：把 prev+36 位移 ==')
for d in (-24,-12,-8,-4,4,8,12,24):
    ok=sum(1 for a,lo,p,ent,n in lst if all(((b-(lo+d))%24==0) and (lo+d)<=b<p+4*n for b in ent))
    print('  shift %+3d : %d/953'%(d,ok))
print('== E. 未被任何类引用的 BCD 槽（全池）==')
allref=set(b for a in CHD for b in BCA[a])
region=[(a,PREV[a]+36,P.dw(a+12)) for a in CHD[1:]]
slots=set()
for a,lo,p in region:
    for i in range((p-lo)//24): slots.add(lo+24*i)
print(' 槽总数 %d，被引用 %d，未引用 %d'%(len(slots),len(slots&allref),len(slots-allref)))
print(' 未引用样例',[hex(x) for x in sorted(slots-allref)[:10]])
print('== F. 未引用槽的内容形态（是否也是合法 BCD）==')
def isbcd(b):
    td=P.dw(b); nc=P.dw(b+4); md=s32(P.dw(b+8)); pd=s32(P.dw(b+12))
    return P.where(td)=='.data' and td in ptdset and nc is not None and nc<30 and pd in (-1,0) or (pd is not None and abs(pd)<100000)
c1=collections.Counter()
for x in sorted(slots-allref):
    c1[(P.where(P.dw(x)),P.dw(x) in ptdset,P.dw(x+12)==0xffffffff)]+=1
print(' ',c1.most_common(6))
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
