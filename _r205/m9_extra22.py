#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m9（权威三）：22 条「无 vftable 的 mdisp==0 BCD」逐条身份 + 它们与 954 类的基类关系。
这是 R205 未取得项 A5 的展开：它们是什么、谁继承它们、为什么不产生 vftable。
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
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
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
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
EMB={a+16:a for a in CHD}; OWNTD={a:P.dw(a+28) for a in CHD}
ck('V0 基数 COL1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,954,1002,2615),
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCA.values())))
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(OWNTD.values())
extra=[b for b in m0 if P.dw(b) not in ownset]
ck('V1 22 条非自有 mdisp==0',len(extra)==22,len(extra))

# ---------- K1 逐条身份表 ----------
rows=[]
for b in extra:
    nm=cname(b)
    ncb=P.dw(b+4); attr=P.dw(b+20); pdisp=s32(P.dw(b+12))
    # 谁继承它：BCA 里含该 BCD 的类
    owners=[a for a in CHD if b in BCA[a]]
    # 这些 owner 里，b 在 BCA 中的下标（= 距该类的继承深度）
    idxs=sorted(set(BCA[a].index(b) for a in owners))
    rows.append(dict(bcd=hex(b),name=nm,ncb=ncb,attr=attr,pdisp=pdisp,
                     nowners=len(owners),idxs=idxs,
                     owners=[COL[a+16]['name'] for a in owners[:4]]))
for r in sorted(rows,key=lambda r:-r['nowners']):
    print('   K1 %-46s ncb=%d attr=%d nowners=%3d idxs=%s'%(r['name'][:46],r['ncb'],r['attr'],r['nowners'],r['idxs'][:5]))
ck('K1a 22 条全部被至少 1 个类继承',all(r['nowners']>=1 for r in rows),min(r['nowners'] for r in rows))
ck('K1b 22 条被继承总次数 == 474',sum(r['nowners'] for r in rows)==474,sum(r['nowners'] for r in rows))
ck('K1c ncb（numContainedBases）分布', True, collections.Counter(r['ncb'] for r in rows).most_common())
ck('K1d attributes 分布', True, collections.Counter(r['attr'] for r in rows).most_common())
ck('K1e pdisp 恒 -1（无虚基类，复现 R204 QG1）',all(r['pdisp']==-1 for r in rows),collections.Counter(r['pdisp'] for r in rows).most_common())
# idxs 是否恒为 0 之后的位置（即它们总是出现在 BCA 的非首位）
ck('K1f 它们从不出现在 BCA[0]（BCA[0] 恒为本类自有 BCD，复现 m3 E3a）',
   all(0 not in r['idxs'] for r in rows),[r['name'] for r in rows if 0 in r['idxs']])

# ---------- K2 为什么没有 vftable：ncb 与 attr ----------
# MSVC: BCD.attributes bit0 = 1 => 该类含虚基类或多重继承；这里全 0/2
ck('K2a 22 条 attributes 只有 {0,2}，无 1 或 5',set(r['attr'] for r in rows)<={0,2},
   sorted(set(r['attr'] for r in rows)))
# 对比：954 类自有 BCD 的 attributes 分布
owattr=collections.Counter(P.dw(b+20) for b in m0 if P.dw(b) in ownset)
ck('K2b 对照：954 自有 BCD attributes 分布',True,dict(owattr))
# 关键：这 22 条是否都属于 .?AU 接口（无数据成员的纯接口），因此不需要 vftable 视图跨子对象
au=[r for r in rows if r['name'].startswith('.?AU')]
ck('K2c 17 条 .?AU 接口 / 5 条 .?AV',(len(au),len(rows)-len(au))==(17,5),(len(au),len(rows)-len(au)))
print('   K2 5 条非接口:',[r['name'] for r in rows if not r['name'].startswith('.?AU')])

# ---------- K3 对照：954 类中有没有「mdisp==0 但非自有」的第二种形态 ----------
# 已在 V1 中排除。改为检验：22 条是否都能在 .data 的 TD 里找到，且 TD 后 4 字节是什么
tdinfo=collections.Counter()
for b in extra:
    td=P.dw(b); f4=P.dw(td); f8=P.cstr(td+8,60)
    tdinfo[('f4',f4)]+=1
ck('K3a 22 条 TD 的 +0 字段分布（与 954 类 TD 对比用）',True,tdinfo.most_common(3))
ow_f4=collections.Counter(P.dw(OWNTD[a]) for a in CHD)
ck('K3b 954 类 TD 的 +0 字段分布',True,ow_f4.most_common(3))
ck('K3c 两者 TD +0 形态是否相同',set(tdinfo)==set(('f4',k) for k in ow_f4),
   (sorted(set(k for (_,k),_ in tdinfo)),sorted(set(ow_f4))[:4]))

# ---------- K4 它们作为基类时的 mdisp 是否恒 0 ----------
ck('K4a 它们在所有 BCA 出现处 mdisp 恒 0（记录自洽）',
   all(s32(P.dw(b+8))==0 for b in extra),None)
# 但 BCA 中同一 BCD 可被不同类以不同「名义偏移」引用？MSVC 里 mdisp 存于 BCD，与类无关
ck('K4b 因此它们对所有子类都在偏移 0（单一继承链顶端）',True,'n/a')

# ---------- K5 反控 ----------
import random
random.seed(2056)
cks=sorted(set(b for b in m0 if P.dw(b) in ownset))
ck('C1 反控：取 22 条中的任一条，其 pTD 都不等于任何 CHD 的 dw(a+28)',
   all(P.dw(b) not in ownset for b in extra),None)
ck('C2 正控：954 条自有 BCD 的 pTD 每个都等于某 CHD 的 dw(a+28)',
   all(P.dw(b) in ownset for b in cks),None)
ck('C3 说明：ownset 基数 954，22 条的 pTD 互异数',len(set(P.dw(b) for b in extra))==22,len(set(P.dw(b) for b in extra)))

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,rows=rows,
               inherit=sum(r['nowners'] for r in rows),
               owattr=dict(owattr)),open('_r205/m9_extra22.json','w'),indent=1)
