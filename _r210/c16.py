# -*- coding: utf-8 -*-
"""R210 c16（律 U 强化）：不预设 12 个 QI 目标，而是对全部 954 个主视图类的 slot0 函数
判定「是否形似 QI」（体内出现 repe cmpsd 且有出参写），再检验律 U 是否普遍成立。
这把 R210 c9 的 91/91（在 12 个目标的子集上）升级为「所有 QI 类」的普遍检验。
反控：非 QI 类（slot0 无 repe cmpsd）必须视图集合 == {0}。
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
ck('I0 类 954 / 主视图唯一', len(cls)==954 and len(main)==954, '%d/%d'%(len(cls),len(main)))
def is_qi_like(a):
    o=P.r2o(a); ins=[]
    n=0
    for i in md.disasm(P.RAW[o:o+900],a):
        ins.append(i); n+=1
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if n>240: break
    return any(i.mnemonic.startswith('repe') or i.mnemonic.startswith('rep') for i in ins)
def offs(a):
    o=P.r2o(a); ins=[]
    n=0
    for i in md.disasm(P.RAW[o:o+900],a):
        ins.append(i); n+=1
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if n>240: break
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
    return res
qi={}
for p,c in main.items(): qi[p]=is_qi_like(VT[c][0])
qcls=[p for p in main if qi[p]]
nq=[p for p in main if not qi[p]]
print('# slot0 形似 QI 的类 = %d ；非 QI = %d'%(len(qcls),len(nq)))
ck('I1 QI 类数 > 91（12 目标之外还有别的 QI）', len(qcls)>=91, len(qcls))
ok=0; bad=[]
for p in qcls:
    O=offs(VT[main[p]][0]); pred={4}|{x for x in O if x>0}
    got=set(cls[p])
    if pred==got: ok+=1
    else: bad.append((hex(p),NM[main[p]],sorted(got),sorted(pred),hex(VT[main[p]][0])))
ck('I2 律 U 在全部 QI 类上成立', ok==len(qcls), 'ok=%d/%d bad=%s'%(ok,len(qcls),bad[:6]))
ok2=0; bad2=[]
for p in nq:
    got=set(cls[p])
    if got=={0}: ok2+=1
    else: bad2.append((hex(p),NM[main[p]],sorted(got),hex(VT[main[p]][0])))
ck('I3 反控：非 QI 类视图集合恒 {0}', ok2==len(nq), 'ok=%d/%d bad=%s'%(ok2,len(nq),bad2[:6]))
# 0x4f4240 那 9 个类
t=0x4f4240
same=[p for p in main if VT[main[p]][0]==t]
ck('I4 0x4f4240 承载 %d 类，且其视图集 = 其 QI 偏移（无额外视图）'%len(same),
   len(same)>0 and all(set(cls[p])=={4}|{x for x in offs(t) if x>0} for p in same),
   (len(same), sorted(offs(t)), [sorted(cls[p]) for p in same][:3]))
json.dump(dict(qcls=[hex(p) for p in qcls], nq=[hex(p) for p in nq],
               ok=ok, n_q=len(qcls), n_nonq=len(nq), bad=bad, bad2=bad2,
               off_4f4240=sorted(offs(0x4f4240))),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c16.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
