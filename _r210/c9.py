# -*- coding: utf-8 -*-
"""R210 c9: 律 U 严格式（T 形态口径）与 {4} 项的性质判定。
严格式：对 91 个含 T 视图的类，T 视图偏移集合 == {4} ∪ (slot0 QI 委托闭包的正偏移)。
两个子判定：
  (a) 91/91 类恰有 1 张 mdisp=4 视图（普遍项，与 QI 无关）；
  (b) 非 4 的 T 偏移（10 个）= QI 闭包正偏移，逐类零残留；
  (c) 反控：若把 {4} 换成 QI 闭包（即认为 4 由 QI 返回），HouseClass 等类必失配。
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
    ins=insns(a); offs=set(); lreg=None; loff=None; calls=[]
    for i in ins:
        if i.mnemonic=='call':
            m=re.match(r'^0x([0-9a-f]+)$', i.op_str)
            if m and int(m.group(1),16) in QS: calls.append(int(m.group(1),16))
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]', i.op_str)
            if m:
                lreg=m.group(1); g=m.group(2); loff=int(g,16) if g.startswith('0x') else int(g)
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr ['):
            rhs=i.op_str.split(', ')[1]; v=0
            if lreg and rhs==lreg and loff is not None: v=loff
            offs.add(v); lreg=None; loff=None
    return offs,calls
OFF={}; EDG={}
for t in QS:
    o,c=analyze(t); OFF[t]=o; EDG[t]=c
def closure(t):
    seen=set(); st=[t]; out=set()
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); out|=OFF[x]; st.extend(EDG[x])
    return out
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
tcls=[p for p,v in cls.items() if any(c in HIT for c in v.values())]
ck('AA0 含 T 视图的类 = 91', len(tcls)==91, len(tcls))
a_ok=sum(1 for p in tcls if 4 in cls[p] and sum(1 for c in cls[p].values() if c in HIT and MD[c]==4)==1)
ck('AA1 (a) 91 类各恰 1 张 mdisp=4 视图', a_ok==91, a_ok)
b_ok=0; b_bad=[]
for p in tcls:
    tset={MD[c] for c in cls[p].values() if c in HIT}
    q=VT[cls[p][0]][0]
    pred={4}|{o for o in closure(q) if o>0}
    if tset==pred: b_ok+=1
    else: b_bad.append((hex(p),NM[cls[p][0]],sorted(tset),sorted(pred),hex(q)))
ck('AA2 (b) 91/91：T 偏移集合 == {4} ∪ QI 委托闭包正偏移', b_ok==91, 'ok=%d bad=%s'%(b_ok,b_bad[:4]))
non4=[(p,m) for p in tcls for m in {MD[c] for c in cls[p].values() if c in HIT} if m!=4]
ck('AA3 非 4 的 T 视图 = 10 张', len(non4)==10, [(hex(p),m) for p,m in non4])
e_ok=0; e_bad=[]
for p,m in non4:
    q=VT[cls[p][0]][0]
    if m in closure(q): e_ok+=1
    else: e_bad.append((hex(p),NM[cls[p][0]],m,sorted(closure(q))))
ck('AA4 非 4 的每个 T 偏移都在 QI 闭包内（10/10）', e_ok==10, 'ok=%d bad=%s'%(e_ok,e_bad))
c_bad=[]
for p in tcls:
    q=VT[cls[p][0]][0]
    tset={MD[c] for c in cls[p].values() if c in HIT}
    if tset=={o for o in closure(q) if o>0}: c_bad.append((hex(p),NM[cls[p][0]],sorted(tset),sorted(closure(q))))
ck('AA5 (c) 反控：去掉普遍项 {4} 后必失配', len(c_bad)>0, len(c_bad))
# 3 个 S3 类（无 T 视图）
s3=[p for p,v in cls.items() if any(c in HIT for c in v.values())==False]
ck('AA6 无 T 视图但有多视图的类 = 3（S3 三表）', len([p for p,v in cls.items() if len(v)>1 and not any(c in HIT for c in v.values())])==3,
   len([p for p,v in cls.items() if len(v)>1 and not any(c in HIT for c in v.values())]))
json.dump(dict(off={hex(k):sorted(v) for k,v in OFF.items()},
               edges={hex(k):[hex(x) for x in v] for k,v in EDG.items()},
               closure={hex(t):sorted(closure(t)) for t in QS},
               tcls=[hex(p) for p in tcls], non4=[[hex(p),m] for p,m in non4],
               a_ok=a_ok,b_ok=b_ok),open('/home/t628/projects/ra2-campaign-forge/_r210/c9.json','w'),indent=0)
print('FAILS',fails)
