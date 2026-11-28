# -*- coding: utf-8 -*-
"""R209 q8（定稿复算）：COL 布局 +12=pTD / +16=pCHD（q7 误用 +8=cdOffset 恒 0，已在自错表登记）。
复算：thunk E9 落点 vs 本类主视图同槽；主视图 slot0/1/2 ret 分布；三形态互斥；0x11c7 定性。
"""
import sys, struct, collections, json
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
# 硬校验 COL 布局
ck('L1 COL +8 恒 0（cdOffset）', all(P.dw(c+8)==0 for c in MD), sum(1 for c in MD if P.dw(c+8)==0))
ck('L2 COL +16 落 .rdata（pCHD）', all(P.where(P.dw(c+16))=='.rdata' for c in MD))
ck('L3 COL +12 落 .data（pTD）', all(P.where(P.dw(c+12))=='.data' for c in MD))
chd=collections.defaultdict(list)
for c in MD: chd[P.dw(c+16)].append(c)
ck('L4 按 +16 分组 = 954 组', len(chd)==954, len(chd))
grp_of={c:P.dw(c+16) for c in MD}
def retimm(a,cap=900):
    o=P.r2o(a)
    for i in md.disasm(P.RAW[o:o+cap],a):
        if i.mnemonic=='ret': return int(i.op_str,16) if i.op_str else 0
    return None
# A. thunk 落点 == 主视图同槽
for slot in (0,1,2):
    ok=0; bad=[]
    for c in HIT:
        prim=[x for x in chd[grp_of[c]] if MD[x]==0]
        if len(prim)!=1: bad.append((hex(c),'prim=%d'%len(prim))); continue
        if TH[VT[c][slot]]['jmp']==VT[prim[0]][slot]: ok+=1
        else: bad.append((hex(c),hex(TH[VT[c][slot]]['jmp']),hex(VT[prim[0]][slot])))
    ck('A%d 101 表的 slot%d thunk 落点 == 本类主视图同槽'%(slot+1,slot), ok==101,
       'ok=%d bad=%s'%(ok,bad[:3]))
ck('A4 954 组每组恰 1 条 mdisp==0', all(len([x for x in v if MD[x]==0])==1 for v in chd.values()),
   sum(1 for v in chd.values() if len([x for x in v if MD[x]==0])==1))
# B. 主视图三槽 ret 分布
rd=[collections.Counter() for _ in range(3)]
prim_tabs=[c for c in VT if MD[c]==0 and len(VT[c])>2]
for c in prim_tabs:
    for s in (0,1,2): rd[s][retimm(VT[c][s])]+=1
for s in (0,1,2):
    print('# 主视图 slot%d ret 分布 = %s'%(s,rd[s].most_common()))
ck('B1 主视图 slot1/slot2 的 ret 4 各 >= 900', rd[1][4]>=900 and rd[2][4]>=900, '%d/%d'%(rd[1][4],rd[2][4]))
ck('B2 主视图 slot0 ret 分布与额外视图不同（0xc 仅为少数）', rd[0][12]<rd[0][4], '%d vs %d'%(rd[0][12],rd[0][4]))
# 额外视图 slot0/1/2
er=[collections.Counter() for _ in range(3)]
for c in HIT:
    for s in (0,1,2): er[s][retimm(TH[VT[c][s]]['jmp'])]+=1
for s in (0,1,2):
    print('# 额外视图(经 thunk) slot%d 落点 ret 分布 = %s'%(s,er[s].most_common()))
ck('B3 额外视图 slot0/1/2 落点 ret 恒 12/4/4', er[0]==collections.Counter({12:101})
   and er[1]==collections.Counter({4:101}) and er[2]==collections.Counter({4:101}),
   [dict(x) for x in er])
# C. 三形态互斥
S={0x410590,0x410580,0x6d1770}
sown={v:{c for c in VT for x in VT[c] if x==v} for v in S}
ck('C1 S 表承载表集合两两不重叠',
   sum(len(s) for s in sown.values())==len(set().union(*sown.values())),
   [len(s) for s in sown.values()])
ck('C2 S 表承载表无一含 thunk', all(not (s & set(HIT)) for s in sown.values()),
   [len(s & set(HIT)) for s in sown.values()])
I={0x41bc30,0x522a60,0x746100}
iown={v:{c for c in VT for x in VT[c] if x==v} for v in I}
ck('C3 I 三个函数各被 1 张表引用且不含 thunk', all(len(v)==1 for v in iown.values())
   and all(not (v & set(HIT)) for v in iown.values()), [len(v) for v in iown.values()])
ck('C4 T/S/I 三形态承载表集合两两不交（305+159 槽无重叠）',
   not (set(HIT) & (set().union(*sown.values()) | set().union(*iown.values()))),
   len(set(HIT) & (set().union(*sown.values()) | set().union(*iown.values()))))
# D. 0x11c7 定性
o=P.r2o(0x6d1770); code=P.RAW[o:o+400]
ck('D1 0x6d1770 内含 0x11c7 与 0x11c8 两个立即数',
   b'\xc7\x11\x00\x00' in code and b'\xc8\x11\x00\x00' in code)
ck('D2 0x11c7 不是任何类的 pTD 地址（类 pTD 全落 .data）',
   all(P.where(0x11c7)!='.data' for _ in [0]) and P.where(0x11c7)=='other')
ctx=P.RAW[P.r2o(0x6379f6):P.r2o(0x6379f6)+16]
ck('D3 0x11c7 在 0x6379fc 被 push 作虚调用实参', ctx==bytes.fromhex('8b116a0068c7110000ff12'),
   ctx.hex(' '))
json.dump(dict(prim_ret=[{str(k):v for k,v in r.items()} for r in rd],
               extra_ret=[{str(k):v for k,v in r.items()} for r in er]),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q8.json','w'),indent=1)
print('\n== FAILS: %s (%d 断言) =='%(fails,NA))
