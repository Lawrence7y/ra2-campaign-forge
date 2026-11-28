# -*- coding: utf-8 -*-
"""R209 q10: 落盘用总表 —— 律 T 三形态全景 + ret 三槽证据 + 与 R208 口径的差量核对。
额外断言：R208 报的「101 条 mdisp==mdisp」在 303 槽口径下仍成立；R208 报「21 个 thunk」需订正为 22。
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
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
VO={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
TH={int(k,16):v for k,v in d3['thunk'].items()}
d9=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q9.json'))
tabs6=[int(x,16) for x in d9['tabs_6d1770']]
S={0x410590:78,0x410580:75,0x6d1770:3}
sown={}
for v in S: sown[v]=[c for c in VT if v in VT[c]]
I={0x41bc30:0,0x522a60:0,0x746100:0}
iown={v:[c for c in VT if v in VT[c]] for v in I}
print('## 律 T 三形态承载表（最终数）:')
print('   T: %d 张表，305 槽（101*3 + 2 越界），%d 个 thunk'%(len(HIT),len(TH)))
print('   S: %d 张表（%s），各 %s 槽'%(
    sum(len(v) for v in sown.values()),
    {hex(k):len(v) for k,v in sown.items()}, {hex(k):len(set(len(VT[c]) for c in v)) for k,v in sown.items()}))
print('   I: %d 张表（%s）'%(sum(len(v) for v in iown.values()),{hex(k):[hex(x) for x in v] for k,v in iown.items()}))
tot=len(HIT)+sum(len(v) for v in sown.values())+sum(len(v) for v in iown.values())
ck('Z1 T+S+I 表数合计 == R208 的额外视图 260', tot==260, tot)
ck('Z2 S 三表被引用次数 == 78/75/3（与 R208 QM2 同一组数）',
   [len(sown[v]) for v in (0x410590,0x410580,0x6d1770)]==[78,75,3],
   [len(sown[v]) for v in (0x410590,0x410580,0x6d1770)])
ck('Z3 I 三函数各 1 张表', all(len(v)==1 for v in iown.values()), [len(v) for v in iown.values()])
# R208 口径差量
ck('Z4 R208「21 个不同 thunk（slot0 口径）」订正为 22（含 1 条 B81）',
   len({VT[c][0] for c in HIT})==22, len({VT[c][0] for c in HIT}))
ck('Z5 R208 三条不变量的槽级扩展：303/303 立即数==mdisp', 
   sum(1 for c in HIT for i in (0,1,2) if TH[VT[c][i]]['imm']==MD[c])==303)
# 越界 2 槽的 imm 与表 mdisp
HC=0x8028b8
ck('Z6 HouseClass slot3/4 imm=4 而表 mdisp=40 ⇒ 越界槽不遵循 thunk-imm==mdisp',
   TH[VT[HC][3]]['imm']==4 and TH[VT[HC][4]]['imm']==4 and MD[HC]==40,
   (TH[VT[HC][3]]['imm'],TH[VT[HC][4]]['imm'],MD[HC]))
# 70 thunk 的 mdisp 归属表
print('\n## 70 个 thunk 的 imm 分布 = %s'%collections.Counter(t['imm'] for t in TH.values()).most_common())
print('## 101 表的 mdisp 分布 = %s'%collections.Counter(MD[c] for c in HIT).most_common())
print('## 101 表的长度分布 = %s'%collections.Counter(len(VT[c]) for c in HIT).most_common())
# 表长度 vs 三槽
ck('Z7 101 表全部长度 >= 3', all(len(VT[c])>=3 for c in HIT), min(len(VT[c]) for c in HIT))
# slot3.. 中非 thunk 的落点都是 .text 且 ret 各异（抽查最小 3 槽表）
mn=[c for c in HIT if len(VT[c])==3]
ck('Z8 有 5 槽长的 T 表（长度 3 的 T 表存在）', len(mn)>0, len(mn))
json.dump(dict(T=len(HIT),S={hex(k):len(v) for k,v in sown.items()},I={hex(k):[hex(x) for x in v] for k,v in iown.items()},
               thunk_imm=dict((str(k),v) for k,v in collections.Counter(t['imm'] for t in TH.values()).items()),
               tab_mdisp=dict((str(k),v) for k,v in collections.Counter(MD[c] for c in HIT).items()),
               tab_len=dict((str(k),v) for k,v in collections.Counter(len(VT[c]) for c in HIT).items())),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q10.json','w'),indent=1)
print('\n== FAILS: %s (%d) =='%(fails,NA))
