# -*- coding: utf-8 -*-
"""R210 c13: 律 U 的唯一例外 —— HouseClass 的 +4 视图存在但它的 QI 不返回 +4。
判据三条独立线：(1) BCD 侧 HouseClass 在 mdisp=4 上确有一条 IRTTITypeInfo 记录；
(2) 该视图 slot0 thunk 的 E9 落点 = 0x4f6830（与主视图同一个 QI）；
(3) 0x4f6830 体内比较的 6 个 IID 与返回偏移为 {0,36,40,44}，无 +4 分支。
反控：78 个「BCD 真接口 = IRTTITypeInfo」的类里，另外 77 个的 QI 都返回 +4。
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
d12=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c12.json'))
iid4={int(k,16):set(int(x,16) for x in v) for k,v in d12['iid4'].items()}
bd=d12['bd']
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
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
main={p:v[0] for p,v in cls.items() if 0 in v}
# (1) BCD 侧
irtt=set(bd['.?AUIRTTITypeInfo@@'])
ck('CC1 BCD 侧声明 IRTTITypeInfo@+4 的类 = 78', len(irtt)==78, len(irtt))
ck('CC2 其中 HouseClass 在列', '.?AVHouseClass@@' in irtt)
# (2) HouseClass +4 视图
hp=[p for p in main if NM[main[p]]=='.?AVHouseClass@@']
ck('CC3 HouseClass 类 pCHD 恰 1 个', len(hp)==1, [hex(x) for x in hp])
p=hp[0]
ck('CC4 HouseClass 有 mdisp=4 视图', 4 in cls[p], sorted(cls[p]))
v4=cls[p][4]
ck('CC5 该 +4 视图 slot0 是 thunk，落点 = 0x4f6830', VT[v4][0] in TH and TH[VT[v4][0]]['jmp']==0x4f6830,
   (hex(VT[v4][0]), hex(TH[VT[v4][0]]['jmp']) if VT[v4][0] in TH else None))
s0=VT[main[p]][0]
ck('CC6 HouseClass 主视图 slot0 直接就是 0x4f6830（非 thunk）', s0==0x4f6830 and s0 not in TH, hex(s0))
# (3) 0x4f6830 无 +4 分支
ck('CC7 0x4f6830 的返回偏移集合无 4', 4 not in iid4.get(0x4f6830,set()) and 0x4f6830 in iid4 and iid4[0x4f6830]==set(),
   sorted(iid4.get(0x4f6830,set())))
# 反控：77 个
cnt=0; miss=[]
for name in irtt:
    pp=[x for x in main if NM[main[x]]==name]
    if len(pp)!=1: miss.append((name,'nomain')); continue
    s=VT[main[pp[0]]][0]
    if s not in iid4: miss.append((name,'noQI')); continue
    if iid4[s]=={0x7e9ae0}: cnt+=1
    else: miss.append((name, sorted(hex(x) for x in iid4[s])))
ck('CC8 反控：78 个 IRTTITypeInfo 类里 QI 返回 +4 的（IID 0x7e9ae0）= 77，唯一例外 HouseClass',
   cnt==77 and len(miss)==1 and miss[0][0]=='.?AVHouseClass@@', 'cnt=%d miss=%s'%(cnt,miss))
# 12 个 ILocomotion 与 1 个 ILinkStream 是否全配平
loc=set(bd['.?AUILocomotion@@']); ls=set(bd['.?AUILinkStream@@'])
def allret(names,iid):
    o=0; b=[]
    for name in names:
        pp=[x for x in main if NM[main[x]]==name]
        if len(pp)!=1: b.append((name,'nomain')); continue
        s=VT[main[pp[0]]][0]
        if iid in iid4.get(s,set()): o+=1
        else: b.append((name,sorted(hex(x) for x in iid4.get(s,set()))))
    return o,b
o1,b1=allret(loc,0x7ed358); o2,b2=allret(ls,0x7e9530)
ck('CC9 ILocomotion 12 类全部 QI 返回 +4（IID 0x7ed358）', o1==12 and not b1, (o1,b1))
ck('CC10 ILinkStream 1 类 QI 返回 +4（IID 0x7e9530）', o2==1 and not b2, (o2,b2))
json.dump(dict(house=hex(p), v4=hex(v4), irtt=sorted(irtt), cnt=cnt, miss=miss),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c13.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
