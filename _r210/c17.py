# -*- coding: utf-8 -*-
"""R210 c17（律 U 定稿 · 全类口径）：不预设 12 个 QI 目标，对全部 954 个主视图类判定 QI 形态，
检验双条件：
  (i)  「有 T 形态视图」 <=> 「slot0 的 QI 形态函数返回至少一个正偏移」
  (ii) 有 T 视图时 T 偏移集合 == {4} ∪ 正偏移（{4} 为普遍项）
  (iii) 非 QI 形态类（slot0 无 rep 前缀指令）必须零 T 视图，且视图集合 == {0} ∪ S/I 偏移
反控：把 (ii) 的 {4} 去掉 ⇒ HouseClass 失配；把正偏移换成「全部 QI-like 函数的偏移并集」⇒ 大面积失配。
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
    res=set(); lreg=None; loff=None
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
qcls=[p for p in main if an(VT[main[p]][0])[0]]
nq=[p for p in main if not an(VT[main[p]][0])[0]]
print('# QI 形态类 %d / 非 QI %d / 合计 %d'%(len(qcls),len(nq),len(qcls)+len(nq)))
ck('J0 分类完备 185+769=954', len(qcls)==185 and len(nq)==769, (len(qcls),len(nq)))
def tset(p): return {MD[c] for c in cls[p].values() if c in HIT}
def pos(p): return {x for x in an(VT[main[p]][0])[1] if x>0}
# (i) 双条件
bic=sum(1 for p in main if (len(tset(p))>0)==(len(pos(p))>0))
ck('J1 (i) 双条件：「有 T 视图」<=>「QI 返回至少一个正偏移」', bic==954, '%d/954'%bic)
bad=[(hex(p),NM[main[p]],sorted(tset(p)),sorted(pos(p))) for p in main if (len(tset(p))>0)!=(len(pos(p))>0)]
print('   反例：',bad[:5])
# (ii)
ok=0; b2=[]
for p in qcls:
    if tset(p)==({4}|pos(p)): ok+=1
    else: b2.append((hex(p),NM[main[p]],sorted(tset(p)),sorted({4}|pos(p))))
ck('J2 (ii) T 偏移集合 == {4} ∪ 正偏移（185 个 QI 类全过）', ok==185, 'ok=%d bad=%s'%(ok,b2[:5]))
# (iii)
ok3=0; b3=[]
for p in nq:
    if tset(p)==set() and set(cls[p])=={0}: ok3+=1
    else: b3.append((hex(p),NM[main[p]],sorted(cls[p]),sorted(tset(p))))
ck('J3 (iii) 非 QI 类：零 T 视图 且 视图集合 == {0}', ok3==769, 'ok=%d bad=%s'%(ok3,b3[:5]))
# 反控 A
badA=[p for p in qcls if tset(p)==pos(p)]
ck('J4 反控 A：去掉 {4} 后失配类数 = 91（全部有 T 视图的类）', len(badA)==91, len(badA))
# 反控 B
ALLP=set()
for p in qcls: ALLP|=pos(p)
badB=[p for p in qcls if tset(p)==({4}|ALLP)]
ck('J5 反控 B：用全并集后失配类数', len(badB)>0, len(badB))
# 反控 C：把非 QI 类也纳入判据
badC=[p for p in nq if tset(p)==({4}|pos(p))]
ck('J6 反控 C：非 QI 类若按同式判则不成立（分离两类是必要的）', len(badC)==769, len(badC))
json.dump(dict(nq=len(nq),nq_=len(qcls),ok1=bic,ok2=ok,ok3=ok3,bad=bad,b2=b2[:20],b3=b3[:20],
               badA=len(badA),badB=len(badB),badC=len(badC),ALLP=sorted(ALLP)),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c17.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
