# -*- coding: utf-8 -*-
"""R210 c18（律 U 定稿 v2）：T 视图偏移集合 == ({4} ∪ QI 正偏移) 当 QI 正偏移非空；否则为空集。
即 {4} 是「QI 至少返回一个正偏移」时附加的固定项。185 个 QI 形态类 + 769 个非 QI 类全量检验。
反控五条见 J*。
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
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
main={p:v[0] for p,v in cls.items() if 0 in v}
cache={}
def an(a):
    if a in cache: return cache[a]
    o=P.r2o(a); ins=[]; n=0
    for i in md.disasm(P.RAW[o:o+900],a):
        ins.append(i); n+=1
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if n>240: break
    isqi=any(i.mnemonic.startswith('rep') for i in ins)
    res=set(); lreg=None; loff=None; pairs=[]
    for i in ins:
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]',i.op_str)
            if m:
                lreg=m.group(1); g=m.group(2); loff=int(g,16) if g.startswith('0x') else int(g)
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr ['):
            rhs=i.op_str.split(', ')[1]; v=0
            if lreg and rhs==lreg and loff is not None: v=loff
            res.add(v); lreg=None; loff=None
    cache[a]=(isqi,res); return cache[a]
def tset(p): return {MD[c] for c in cls[p].values() if c in HIT}
def pos(p): return {x for x in an(VT[main[p]][0])[1] if x>0}
def pred(p):
    q=pos(p)
    return ({4}|q) if q else set()
bad=[(hex(p),NM[main[p]],sorted(tset(p)),sorted(pred(p)),hex(VT[main[p]][0])) for p in main if tset(p)!=pred(p)]
ck('K1 律 U 定稿 v2：T 视图集合 == ({4} ∪ 正偏移) if 正偏移非空 else 空；954/954',
   not bad, 'bad=%d %s'%(len(bad),bad[:6]))
# 分布
d=collections.Counter((bool(pos(p)), tuple(sorted(tset(p))), tuple(sorted(pos(p)))) for p in main)
print('# 分布 (有正偏移, T偏移集, 正偏移集) -> 类数：')
for k,v in d.most_common(20): print('   %s -> %d'%(k,v))
ck('K2 正偏移非空类 = 91，全空类 = 863', sum(1 for p in main if pos(p))==91 and sum(1 for p in main if not pos(p))==863,
   (sum(1 for p in main if pos(p)), sum(1 for p in main if not pos(p))))
ck('K3 正偏移非空的 91 类上 T 视图集合全非空', all(tset(p) for p in main if pos(p)),
   sum(1 for p in main if pos(p) and tset(p)))
ck('K4 正偏移为空的 863 类上 T 视图集合全空', all(not tset(p) for p in main if not pos(p)),
   sum(1 for p in main if not pos(p) and tset(p)))
# 反控
badA=[p for p in main if pos(p) and tset(p)==pos(p)]
ck('K5 反控 A：去掉 {4} 项 ⇒ 有正偏移的 91 类全失配', len(badA)==91, len(badA))
ALLP=set().union(*[pos(p) for p in main])
badB=[p for p in main if not pos(p) and tset(p)==ALLP]
ck('K6 反控 B：把空类也套上全并集 ⇒ 863 类全失配', len(badB)==863, len(badB))
badC=[p for p in main if pos(p) and tset(p)=={4}]
ck('K7 反控 C：只留 {4}（忽略正偏移）⇒ 失配 10 类（多视图的 10 张非 4）', len(badC)==10, len(badC))
badD=[p for p in main if tset(p)==pred(p) and not an(VT[main[p]][0])[0] and tset(p)]
ck('K8 反控 D：非 QI 形态类从未有 T 视图（无需额外假设）', not badD, len(badD))
# BaseClass 那条 1 的成因
p=[x for x in main if NM[main[x]]=='.?AVBaseClass@@'][0]
o=P.r2o(VT[main[p]][0])
print('# BaseClass slot0=%08x 前 20 条：'%VT[main[p]][0])
n=0
for i in md.disasm(P.RAW[o:o+200],VT[main[p]][0]):
    print('   %08x %-10s %s'%(i.address,i.mnemonic,i.op_str)); n+=1
    if n>19: break
json.dump(dict(bad=bad,badA=len(badA),badB=len(badB),badC=len(badC),
               dist=[[str(k),v] for k,v in d.most_common()], ALLP=sorted(ALLP)),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c18.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
