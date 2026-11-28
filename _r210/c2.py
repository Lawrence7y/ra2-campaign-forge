# -*- coding: utf-8 -*-
"""R210 c2: 律 U —— 额外视图集合 == {4} ∪ {本类 slot0 QI 静态返回的正偏移}。
正向：91 类 / 101 视图零残留；反向控制：slot0 落在 12 个 QI 目标但无额外视图的类，其 QI 返回偏移必须只有 0/4。
解析器升级：lea <reg>,[<this>+K] 后紧跟 mov [out],<reg> 才算一条返回偏移；mov [out],<this> 为 0。
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
def insns(a,cap=900):
    o=P.r2o(a); out=[]
    for i in md.disasm(P.RAW[o:o+cap],a):
        out.append(i)
        if i.mnemonic=='ret' and i.address>a+0x20: break
    return out
def qi_offsets(a):
    """返回 (返回偏移集合, IID 与偏移配对明细)。位移 4 是十进制 '4'，必须同时接受十进制与十六进制。"""
    ins=insns(a); res=set(); pairs=[]; cur=None; lreg=None; loff=None
    for i in ins:
        if i.mnemonic=='mov' and i.op_str.startswith('edi, 0x'):
            cur=int(i.op_str.split(', ')[1],16); pairs.append([cur,None])
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]', i.op_str)
            if m:
                lreg=m.group(1); g=m.group(2)
                loff=int(g,16) if g.startswith('0x') else int(g)
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr ['):
            rhs=i.op_str.split(', ')[1]
            v=0
            if lreg and rhs==lreg and loff is not None: v=loff
            res.add(v)
            if pairs and pairs[-1][1] is None: pairs[-1][1]=v
            lreg=None; loff=None
        if i.mnemonic=='call' and pairs and pairs[-1][1] is None:
            pairs[-1][1]=0; res.add(0)
    return res,pairs
QI=collections.defaultdict(list)
for c in HIT:
    for i,v in HIT[c]:
        if i==0: QI[TH[v]['jmp']].append(c)
OFF={}; PAIRS={}
for t in QI:
    o,p=qi_offsets(t); OFF[t]=o; PAIRS[t]=p
print('# 12 个 QI 目标返回偏移：')
for t in sorted(QI): print('  %08x ntab=%-2d offs=%s'%(t,len(QI[t]),sorted(OFF[t])))
cls=collections.defaultdict(set)
cls_col=collections.defaultdict(list)
for c in HIT:
    p=P.dw(c+16); cls[p].add(MD[c]); cls_col[p].append(c)
ck('U0 有额外视图的类数=91，视图总数=101', len(cls)==91 and sum(len(v) for v in cls.values())==101,
   'cls=%d views=%d'%(len(cls),sum(len(v) for v in cls.values())))
ok=0; bad=[]
for p,ms in cls.items():
    qis={TH[VT[c][0]]['jmp'] for c in cls_col[p]}
    if len(qis)!=1: bad.append(('multi',hex(p))); continue
    t=list(qis)[0]
    want={4}|{o for o in OFF[t] if o>0}
    if want==ms: ok+=1
    else: bad.append((hex(p),NM[cls_col[p][0]],sorted(ms),sorted(OFF[t])))
ck('U1 律 U 正向：91 类视图集合 == {4} ∪ QI 正偏移', ok==91 and not bad, 'ok=%d bad=%s'%(ok,bad[:4]))
# 反向：所有主视图类（954），slot0 是否落在 12 个 QI 目标
mainvt={}
cols_by_vt=collections.defaultdict(list)
for c in MD:
    if MD[c]==0: cols_by_vt[vt_of[c]].append(c)
ck('U2 主视图表数 954，vftable 起址互不相同 954', len(cols_by_vt)==954, len(cols_by_vt))
slot0=collections.Counter(vt and VT[c][0] for c,v in list(cols_by_vt.items())[:0])
allmain=[c for c in MD if MD[c]==0]
cnt=collections.Counter(VT[c][0] for c in allmain)
hitq={t:n for t,n in cnt.items() if t in QI}
print('# 主视图 slot0 落在 12 个 QI 目标上的类数 = %d / 954'%sum(hitq.values()))
for t,n in sorted(hitq.items()): print('   %08x n=%-3d offs=%s'%(t,n,sorted(OFF[t])))
# 反向控制：这些类的 QI 若只有 0/4 则不应有额外视图
rev_ok=0; rev_bad=[]
for c in allmain:
    t=VT[c][0]
    if t not in QI: continue
    want={4}|{o for o in OFF[t] if o>0}
    p=P.dw(c+16); got=cls.get(p,set())
    if not got: got={4}
    if want==got: rev_ok+=1
    else: rev_bad.append((hex(c),NM[c],sorted(want),sorted(got)))
ck('U3 反向控制：slot0 是 QI 的每个类，其视图集合都可由 QI 偏移预测',
   not rev_bad, 'ok=%d bad=%d %s'%(rev_ok,len(rev_bad),rev_bad[:4]))
# 那些有额外视图的类，slot0 是否一定在 12 个 QI 中
byp={}
for c in allmain: byp[P.dw(c+16)]=c
ck('U4 有额外视图的 91 类，其主视图 slot0 全在 12 QI 中',
   all(VT[byp[p]][0] in QI for p in cls), sum(1 for p in cls if VT[byp[p]][0] in QI))
setA={p for p in cls}                                   # 有额外视图的类
setB={P.dw(c+16) for c in allmain if VT[c][0] in QI}     # slot0 是 QI 的类
ck('U5 双向等价：{有额外视图的类} == {slot0 是 12 QI 之一的类}',
   setA==setB, 'A=%d B=%d 差A-B=%d 差B-A=%d'%(len(setA),len(setB),len(setA-setB),len(setB-setA)))
ck('U6 每类至少一视图，954 类主视图唯一',
   len({P.dw(c+16) for c in allmain})==954 and len(allmain)==954,
   '%d/%d'%(len({P.dw(c+16) for c in allmain}),len(allmain)))
json.dump(dict(off={hex(k):sorted(v) for k,v in OFF.items()},
               pairs={hex(k):[[hex(a),b] for a,b in v] for k,v in PAIRS.items()},
               cls={hex(k):sorted(v) for k,v in cls.items()},
               cnt_qi={hex(k):v for k,v in hitq.items()},
               rev_ok=rev_ok, rev_bad=rev_bad),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c2.json','w'),indent=0)
print('FAILS',fails)
