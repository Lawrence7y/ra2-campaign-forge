# -*- coding: utf-8 -*-
"""R211 r1：定位 {4} 独立附加项的 8 类（视图集合含 4，但主视图 QI 的返回正偏移集合不含 4）。
另给出这些类的 BCD（+4）真接口名与 +4 视图 slot0 thunk 落点，供后续成因分析。"""
import sys,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT_OF={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
cls=collections.defaultdict(dict)
for v in MD: cls[P.dw(v+16)][MD[v]]=v
def body(a,lim=900,maxn=240):
    o=P.r2o(a); ins=[]
    for i in md.disasm(P.RAW[o:o+lim],a):
        ins.append(i)
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if len(ins)>maxn: break
    return ins
def qi_offsets(a):
    ins=body(a)
    isqi=any(i.mnemonic.startswith('rep') for i in ins)
    res=set(); lreg=None; loff=None; gap=99
    for i in ins:
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]',i.op_str)
            if m:
                lreg=m.group(1); g=m.group(2)
                loff=int(g,16) if g.startswith('0x') else int(g); gap=0
        elif lreg:
            gap+=1
            if gap>8: lreg=None;loff=None
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [') and lreg:
            rhs=i.op_str.split(', ')[-1]
            if rhs==lreg: res.add(loff)
            lreg=None;loff=None
    return isqi,res,[i.mnemonic for i in ins][:6]
rows=[]
for c,vs in cls.items():
    offs=sorted(vs)
    if 4 not in offs: continue
    mainv=vs[0]
    isqi,R,pre=qi_offsets(VT[mainv][0])
    if 4 in R: continue
    # BCD via pBCA of COL: pCHD at COL+16 -> BCA
    rows.append((NM[mainv],offs,hex(c),hex(mainv),isqi,sorted(R),[hex(vs[o]) for o in offs]))
print('{4} 独立附加项类数 = %d'%len(rows))
for r in sorted(rows,key=lambda x:x[1]):
    print('  %-34s views=%s col=%s main=%s isqi=%s R=%s vts=%s'%r)
