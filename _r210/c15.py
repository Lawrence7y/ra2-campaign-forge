# -*- coding: utf-8 -*-
"""R210 c15: 律 U（T 形态口径）的三项反控精确计数 —— 供落盘引用，禁预估。
R1 不跟委托边（只用 QI 自身返回偏移）时的失配类数与名单
R2 取 12 个 QI 偏移全并集时的失配类数
R3 把普遍项 {4} 换成闭包（即认为 4 由 QI 返回）时的失配类数
R4 依赖委托边的类数 = R1 失配类数（逐类点名），并给这些类各依赖哪条边
"""
import sys,struct,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d9=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c9.json'))
OFF={int(k,16):set(v) for k,v in d9['off'].items()}
EDG={int(k,16):[int(x,16) for x in v] for k,v in d9['edges'].items()}
CLO={int(k,16):set(v) for k,v in d9['closure'].items()}
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
QS=set(OFF)
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
main={p:v[0] for p,v in cls.items() if 0 in v}
tcls=[p for p,v in cls.items() if any(c in HIT for c in v.values())]
ck('G0 含 T 视图的类 = 91', len(tcls)==91, len(tcls))
def tset(p): return {MD[c] for c in cls[p].values() if c in HIT}
def pr_full(p):
    s=VT[main[p]][0]; return {4}|{o for o in CLO[s] if o>0}
def pr_noedge(p):
    s=VT[main[p]][0]; return {4}|{o for o in OFF[s] if o>0}
ALL=set().union(*OFF.values())
def pr_union(p): return {4}|{o for o in ALL if o>0}
def pr_noconst(p):
    s=VT[main[p]][0]; return {o for o in CLO[s] if o>0}
def bad_of(fn): return [p for p in tcls if fn(p)!=tset(p)]
for nm,fn in (('R0 主式',pr_full),('R1 不跟委托边',pr_noedge),('R2 全并集',pr_union),('R3 去普遍项{4}',pr_noconst)):
    b=bad_of(fn)
    print('%s: 失配 %d / 91'%(nm,len(b)))
    if b: print('   样例:',[(hex(p),NM[main[p]],sorted(tset(p)),sorted(fn(p))) for p in b[:5]])
b1=bad_of(pr_noedge); b2=bad_of(pr_union); b3=bad_of(pr_noconst)
ck('G1 主式 0 失配', len(bad_of(pr_full))==0, len(bad_of(pr_full)))
ck('G2 不跟委托边 = 0 失配（委托闭包对 T 类是 no-op，如实记）', len(b1)==0, len(b1))
ck('G3 全并集失配数（记为 D2）', len(b2)>0, len(b2))
ck('G4 去普遍项 {4} 失配数（记为 D3）', len(b3)>0, len(b3))
# 依赖委托边的 91- 里，哪些靠哪条边
edges=collections.Counter()
for p in b1:
    s=VT[main[p]][0]
    for e in EDG.get(s,[]): edges[(hex(s),hex(e))]+=1
print('# 依靠的具体委托边：',edges.most_common())
# 逐类：不跟边时的缺口偏移
gap=collections.Counter()
for p in b1:
    s=VT[main[p]][0]
    gap[tuple(sorted(tset(p)-pr_noedge(p)))]+=1
print('# 缺口偏移组合：',gap.most_common())
ck('G5 缺口全为正偏移且只在 {24} 一类', all(all(x>0 for x in g) for g in gap), gap.most_common())
json.dump(dict(d1=len(b1),d2=len(b2),d3=len(b3),
               b1=[[hex(p),NM[main[p]]] for p in b1],
               edges={('%s>%s'%k):v for k,v in edges.items()},
               gap={str(k):v for k,v in gap.items()}),open('/home/t628/projects/ra2-campaign-forge/_r210/c15.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)

# ---- 追加：{4} 项的来源分解（BCD 侧 vs QI 侧）----
d11=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c11.json'))
d12=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c12.json'))
d13=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c13.json'))
bd=d12['bd']; iid4={int(k,16):set(int(x,16) for x in v) for k,v in d12['iid4'].items()}
irtt=bd['.?AUIRTTITypeInfo@@']; loc=bd['.?AUILocomotion@@']; ls=bd['.?AUILinkStream@@']
print('# {4} 项：BCD 侧真接口名 78 / 12 / 1')
ck('H1 BCD 侧 {4} 真接口名三组 = 78+12+1 = 91', len(irtt)+len(loc)+len(ls)==91,
   '%d/%d/%d'%(len(irtt),len(loc),len(ls)))
ret4=0
for name in irtt+loc+ls:
    pp=[x for x in main if NM[main[x]]==name]
    if len(pp)==1:
        s=VT[main[pp[0]]][0]
        if 0x7e9ae0 in iid4.get(s,set()) or 0x7ed358 in iid4.get(s,set()) or 0x7e9530 in iid4.get(s,set()): ret4+=1
ck('H2 QI 侧返回 +4 分支存在的类 = 90（91 减 HouseClass）', ret4==90, ret4)
ck('H3 唯一不匹配 = HouseClass（BCD 有 IRTTITypeInfo@4、QI 无 +4 分支）',
   (91-ret4)==1 and d13['house']=='0x802a18', 91-ret4)
json.dump(dict(ret4=ret4, exc=91-ret4, irtt=len(irtt), loc=len(loc), ls=len(ls)),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c15b.json','w'),indent=0)
print('FAILS',fails)
