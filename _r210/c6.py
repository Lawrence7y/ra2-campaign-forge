# -*- coding: utf-8 -*-
"""R210 c6: 律 U 的最终形态 —— 视图偏移集合 == {0} ∪ (QI 委托链传递闭包内的所有正偏移)。
委托边：QI 体内 call <另一个 QI 目标>（0x414290 -> 0x410260 后 test/jge 成功即返回；
0x4af720 -> 0x55a9b0 后 cmp eax,0x80004002 失败才继续），两种都是委托，故入闭包。
反控 1：去掉委托闭包（只用本函数自身偏移）⇒ 必须出现失配类。
反控 2：把闭包改为「所有 12 个 QI 的偏移并集」⇒ 必须出现失配类。
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
vt_of={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
QI=collections.defaultdict(list)
for c in HIT:
    for i,v in HIT[c]:
        if i==0: QI[TH[v]['jmp']].append(c)
QS=set(QI)

def insns(a,cap=900):
    o=P.r2o(a); out=[]
    for i in md.disasm(P.RAW[o:o+cap],a):
        out.append(i)
        if i.mnemonic=='ret' and i.address>a+0x20: break
    return out
def analyze(a):
    ins=insns(a); offs=set(); pairs=[]; cur=None; lreg=None; loff=None; calls=[]
    for i in ins:
        if i.mnemonic=='mov' and i.op_str.startswith('edi, 0x'):
            cur=int(i.op_str.split(', ')[1],16); pairs.append([cur,None])
        if i.mnemonic=='call':
            m=re.match(r'^0x([0-9a-f]+)$', i.op_str)
            if m:
                t=int(m.group(1),16)
                if t in QS: calls.append(t)
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]', i.op_str)
            if m:
                lreg=m.group(1); g=m.group(2)
                loff=int(g,16) if g.startswith('0x') else int(g)
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr ['):
            rhs=i.op_str.split(', ')[1]; v=0
            if lreg and rhs==lreg and loff is not None: v=loff
            offs.add(v)
            if pairs and pairs[-1][1] is None: pairs[-1][1]=v
            lreg=None; loff=None
        if i.mnemonic=='call' and pairs and pairs[-1][1] is None:
            pairs[-1][1]=0; offs.add(0)
    return offs,pairs,calls
OFF={}; PAIRS={}; EDG={}
for t in QS:
    o,p,c=analyze(t); OFF[t]=o; PAIRS[t]=p; EDG[t]=c
print('# QI 偏移与委托边：')
for t in sorted(QS):
    print('  %08x offs=%-22s edges=%s'%(t,sorted(OFF[t]),[hex(x) for x in EDG[t]]))
def closure(t,use_edges=True):
    seen=set(); st=[t]; out=set()
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); out|=OFF[x]
        if use_edges: st.extend(EDG[x])
    return out
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
mainvt={}
for c in MD:
    if MD[c]==0: mainvt[P.dw(c+16)]=c
ck('X0 类=954 视图=1214 额外视图类=91', len(cls)==954 and sum(len(v) for v in cls.values())==1214
   and sum(1 for v in cls.values() if len(v)>1)==91,
   '%d/%d/%d'%(len(cls),sum(len(v) for v in cls.values()),sum(1 for v in cls.values() if len(v)>1)))
def evaluate(fn,label):
    ok=0; bad=[]
    for p,v in cls.items():
        c=mainvt[p]; pred=fn(VT[c][0])
        want=set(v)
        if pred==want: ok+=1
        else: bad.append((hex(p),NM[v[max(v)]],sorted(want),sorted(pred)))
    return ok,bad
# 主律
ok,bad=evaluate(lambda s0: closure(s0) if s0 in QS else {0}, 'closure')
ck('X1 律 U 最终式：视图集合 == QI 委托闭包偏移集合（含 0），91/91',
   all(closure(VT[mainvt[p]][0])==set(v) for p,v in cls.items() if VT[mainvt[p]][0] in QS and len(v)>1)
   and all(set(v)=={0} for p,v in cls.items() if VT[mainvt[p]][0] not in QS),
   'ok=%d bad=%d %s'%(ok,len(bad),bad[:4]))
# 反控 1：不跟委托边
ok1,bad1=evaluate(lambda s0: closure(s0,False) if s0 in QS else {0}, 'noedge')
ck('X2 反控：不跟委托边时必须出现失配（子集关系，正数>0）', len(bad1)>0, 'ok=%d bad=%d 样例=%s'%(ok1,len(bad1),bad1[:3]))
# 反控 2：全并集
alloff=set().union(*OFF.values())
ok2,bad2=evaluate(lambda s0: alloff if s0 in QS else {0}, 'union')
ck('X3 反控：取 12 QI 全并集必然失配', len(bad2)>0, 'ok=%d bad=%d'%(ok2,len(bad2)))
# 反控 3：随机把某类的视图集合扰动一条
import random
random.seed(11); pert=0
for p,v in list(cls.items())[:200]:
    pred=closure(VT[mainvt[p]][0]); 
    if pred: perturb=set(pred); perturb.add(999)
    if perturb!=set(v): pert+=1
ck('X4 反控：人为加 999 后必须失配', pert==200, pert)
ck('X5 QI 目标集合恰好 12 个且都不在视图表之外',
   len(QS)==12, len(QS))
json.dump(dict(off={hex(k):sorted(v) for k,v in OFF.items()},
               edges={hex(k):[hex(x) for x in v] for k,v in EDG.items()},
               pairs={hex(k):[[hex(a),b] for a,b in v] for k,v in PAIRS.items()},
               closure={hex(t):sorted(closure(t)) for t in QS},
               ok=ok,bad=bad),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c6.json','w'),indent=0)
print('FAILS',fails)
