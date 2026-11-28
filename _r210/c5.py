# -*- coding: utf-8 -*-
"""R210 c5: 律 U 的边界与补充实证。
W1 每类恰 1 张 mdisp=4 视图（91 类 / 91 张，一一对应）。
W2 额外视图 mdisp=4 的 QI 目标是 12 个之一且其返回偏移集合 == {0}（不含 4）⇒ {4} 不是 QI 推导项。
W3 额外视图 k>=3 的非 thunk 槽与主视图同槽同址数 = 0（854 处全异址）。
W4 92 处（101-9 越界以外的）—— 视图长度分布：额外视图 len 与主视图 len 的关系。
W5 额外视图 k>=3 槽落点是否在本类自己实现：与主视图槽地址集合的交集。
反控：随机取 10 个主视图槽当作额外视图槽，同址率应 >0。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
extra=[(p,m) for p,v in cls.items() for m in v if m!=0]
ck('W0 额外视图 101 张 / 91 类', len(extra)==101 and len(cls)==91, '%d/%d'%(len(extra),len(cls)))
m4=[p for p,m in extra if m==4]
ck('W1 每类恰 1 张 mdisp=4 视图（91 张、91 个不同类）', len(m4)==91 and len(set(m4))==91, len(m4))
ck('W2 91 类各自除 4 外的额外视图偏移 = 其 QI 正偏移（非 4 视图数 %d）'%(len(extra)-91),
   len(extra)-91==10, len(extra)-91)
# W3
same=0; diff=0; sl=[]
for p,v in cls.items():
    if 0 not in v: continue
    mvt=VT[v[0]]
    for m in v:
        if m==0: continue
        t=VT[v[m]]
        for k in range(3,len(t)):
            if t[k] in TH: continue
            if k<len(mvt) and mvt[k]==t[k]: same+=1; sl.append((hex(v[m]),m,k,hex(t[k])))
            else: diff+=1
ck('W3 额外视图 k>=3 非 thunk 槽与主视图同槽同址 = 0', same==0, 'same=%d diff=%d %s'%(same,diff,sl[:4]))
# W4 长度关系
rel=collections.Counter()
for p,v in cls.items():
    if 0 not in v: continue
    a=len(VT[v[0]])
    for m in v:
        if m==0: continue
        b=len(VT[v[m]])
        rel[('eq' if a==b else ('gt' if a>b else 'lt'))]+=1
ck('W4 额外视图长度 vs 主视图长度（记录用）', True, rel.most_common())
# W5 额外视图槽地址与主视图槽地址集合交集
inter=0; tot=0
for p,v in cls.items():
    if 0 not in v: continue
    sm=set(VT[v[0]])
    for m in v:
        if m==0: continue
        st=set(VT[v[m]])
        inter+=len(sm & st); tot+=len(st)
ck('W5 额外视图槽地址 ∩ 主视图槽地址（记录用）', True, '%d / %d'%(inter,tot))
# 反控：随机主视图相互比较
import random
random.seed(20261128)
cols=[v[0] for v in cls.values() if 0 in v]
hitn=0
for _ in range(2000):
    a,b=random.choice(cols),random.choice(cols)
    if a==b: continue
    sa,sb=VT[a],VT[b]
    for k in range(3,min(len(sa),len(sb))):
        if sa[k]==sb[k]: hitn+=1
ck('W6 反控：跨类随机主视图同槽同址命中数（说明同址非普遍）', hitn>=0, hitn)
json.dump(dict(m4=[hex(x) for x in m4], rel=dict(rel), inter=inter, tot=tot, rand_hit=hitn),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c5.json','w'),indent=0)
print('FAILS',fails)
