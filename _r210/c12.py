# -*- coding: utf-8 -*-
"""R210 c12: 交叉核 —— mdisp=4 视图的「真接口」BCD 名 必须等于该 QI 体内返回 +4 的那个 IID 所对应的 RTTI 名。
即：QI 里 (IID -> +4) 的 IID，其名下应能由 BCD 侧的 IRTTITypeInfo/ILocomotion/ILinkStream 一一配平。
断言：三组类数 78/12/1 与「按 IID 站点或委托闭包归组」的三组数逐项相等。
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
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
main={p:v[0] for p,v in cls.items() if 0 in v}

def analyze(a):
    o=P.r2o(a); ins=[]
    for i in md.disasm(P.RAW[o:o+900],a):
        ins.append(i)
        if i.mnemonic=='ret' and i.address>a+0x20: break
    pairs=[]; cur=None; lreg=None; loff=None; calls=[]
    for i in ins:
        if i.mnemonic=='mov' and i.op_str.startswith('edi, 0x'):
            cur=[int(i.op_str.split(', ')[1],16),None]
        if i.mnemonic=='call':
            m=re.match(r'^0x([0-9a-f]+)$',i.op_str)
            if m:
                t=int(m.group(1),16)
                if t in QS: calls.append(t)
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]',i.op_str)
            if m:
                lreg=m.group(1); g=m.group(2); loff=int(g,16) if g.startswith('0x') else int(g)
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr ['):
            rhs=i.op_str.split(', ')[1]; v=0
            if lreg and rhs==lreg and loff is not None: v=loff
            if cur and cur[1] is None: cur[1]=v; pairs.append(cur); cur=None
            lreg=None; loff=None
        if i.mnemonic=='call' and cur and cur[1] is None:
            cur[1]=0; pairs.append(cur); cur=None
    return pairs,calls

def iid4(a):
    """返回该 QI（含委托）里返回偏移 4 的那些 IID"""
    out=set(); seen=set(); st=[a]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x)
        p,c=analyze(x)
        for iid,off in p:
            if off==4 and iid: out.add(iid)
        st.extend(c)
    return out

iid4_of={t:iid4(t) for t in QS}
print('# 每个 QI 的「返回 +4 的 IID」：')
for t in sorted(QS): print('   %08x -> %s'%(t,[hex(x) for x in iid4_of[t]]))
def guid(va):
    o=P.r2o(va); b=P.RAW[o:o+16]
    d1,d2,d3_=struct.unpack_from('<IHH',b,0)
    return '%08X-%04X-%04X'%(d1,d2,d3_)
# 归组
grp=collections.defaultdict(list)
for p,c in main.items():
    s=VT[c][0]
    if s not in QS: continue
    iids=iid4_of[s]
    key=tuple(sorted(hex(i) for i in iids)) or ('NO4',)
    grp[key].append(NM[c])
for k,v in grp.items(): print('# 组 %-20s n=%-3d %s'%(','.join(k),len(v),[guid(int(x,16)) for x in k if x!='NO4']))
d11=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c11.json'))
# 按 BCD 名的组
bd=collections.defaultdict(list)
for a,cn,ns in d11['rows']:
    r=[n for n in ns if n!='.?AUIUnknown@@']
    bd[r[0] if r else 'NONE'].append(cn)
ck('BB1 按 QI「+4 IID」分 3 组，按 BCD 真接口名分 3 组', len([k for k in grp if k!=('NO4',)])==3 and len(bd)==3,
   '%d/%d'%(len(grp),len(bd)))
ck('BB2 两组类数逐项相等（78/12/1 vs 78/12/1）',
   sorted(len(v) for v in grp.values())==sorted(len(v) for v in bd.values()),
   ('QI %s'%sorted(len(v) for v in grp.values()), 'BCD %s'%sorted(len(v) for v in bd.values())))
# 逐类配对：同类的 QI 组和 BCD 组必须一致
setmap={}
for a,cn,ns in d11['rows']:
    r=[n for n in ns if n!='.?AUIUnknown@@']
    setmap[cn]=r[0]
bad=[]
for k,v in grp.items():
    if k==('NO4',): continue
    want={setmap[n] for n in v}
    if len(want)!=1: bad.append((k,sorted(want)[:3],v[:3]))
ck('BB3 同一 QI 组内所有类的 BCD 真接口名唯一（组-名一一对应）', not bad, bad[:3])
json.dump(dict(iid4={hex(k):sorted(hex(x) for x in v) for k,v in iid4_of.items()},
               grp={','.join(k):v for k,v in grp.items()},
               bd={k:v for k,v in bd.items()}),open('/home/t628/projects/ra2-campaign-forge/_r210/c12.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
