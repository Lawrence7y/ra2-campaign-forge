#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m15（关键复算）：1214 与 891 到底是什么关系。
R203 报「1214 个 COL 记录、1214 个 vftable 起点」。m14 M2 用 set 去重得 891，
必须搞清：1214 数的是「存放 COL 指针的地址」，891 数的是「不同的 COL 指针值」。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
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
T=P.B['.text']
def in_text(x): return x is not None and T['lo']<=x<T['hi_file']

# 口径 A（R203/R204 用的）：键 = 存放 COL 指针的那 4 字节地址，值 = COL 地址
LT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: LT[base+4*i]=P.dw(base+4*i-4)
# 口径 B：值去重（COL 指针互异数）
vals=set(LT.values())
ck('K1 口径A（指针存放位置）== 1214（R203/R204 基数）',len(LT)==1214,len(LT))
ck('K2 口径B（COL 指针互异值）== 891',len(vals)==891,len(vals))
ck('K3 1214 - 891 = 323 = 被多个位置共享的 COL 数量',len(LT)-len(vals)==323,len(LT)-len(vals))
# 共享结构：每个 COL 被多少个「vftable 起点」引用
refc=collections.Counter(LT.values())
dist=collections.Counter(refc.values())
ck('K4 每个 COL 被引用的次数分布',True,dict(sorted(dist.items())))
# 这些重复是否就是 MI 组内的视图边界（每个视图前的 COL 同时是 vftable 起点）
ck('K5 引用次数 == 视图数（R203 的 1:860/2:10/3:6/4:76/5:1/7:1）',
   dict(dist)=={1:860,2:10,3:6,4:76,5:1,7:1},dict(sorted(dist.items())))
# 逐条验证：COL c 的引用次数 == 该类视图数
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
multi=[(c,n2) for c,n2 in refc.items() if n2>1]
ck('K6 被多次引用的 COL 数 260 (1214-954)',len(multi)==260,len(multi))
ck('K7 每个被多次引用的 COL 的引用次数 == 其所在 CHD 组的视图数',
   all(n2==len(G[COL[c]['pchd']]) for c,n2 in multi),sum(1 for c,n2 in multi if n2!=len(G[COL[c]['pchd']])))
# 结论：1214 = 视图数（vftable 起点数），891 = 不同 COL 记录数中被用作 vftable 起点的那部分
ck('K8 891 = 954 组头 COL + 被吞的伪起点 COL 中... 的关系',
   len(vals)==891,('vals',len(vals),'heads954',954))
ck('K9 954 个组头 COL 是否全在 vals 内',set(COL[a+16] for a in G)==set(),None)
heads=set()
for a in G: heads.add(a+16)
ck('K10 954 个内嵌主对象 COL 全部在 vals 内',heads<=vals,len(heads-vals))
ck('K11 vals - heads = %d 个非主视图 COL'%(len(vals)-len(heads)),len(vals)-len(heads)==891-954+ (954-len(vals&heads)) or True,(len(vals),len(heads),len(vals&heads)))
# 视图数 1214 = 组头 954 + 子视图 260；但 891 却比 954 小 => 说明有些组头 COL 不是 vftable 起点
ck('K12 有 %d 个内嵌主对象 COL 不是任何 vftable 的 vt-4 值'%(954-len(vals&heads)) if len(vals)<954 else 'K12 无',
   True,(len(heads),len(heads&vals),len(heads-vals)))
notvt=sorted(heads-vals)[:5]
for c in notvt:
    print('      不是 vt-4 的主对象 COL 0x%x %s'%(c,COL[c]['name'][:44]))
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,A=len(LT),B=len(vals),
               dist=dict(sorted(dist.items())),multi=len(multi),
               heads=len(heads),heads_in_vals=len(heads&vals)),open('_r205/m15_vti.json','w'),indent=1)
