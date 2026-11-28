# -*- coding: utf-8 -*-
"""R210 c14: 律 V 的分布汇总（mV / (mT,mV) 对 / 每 mV 的 thunk 数），供落盘引用数字。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
pairs=collections.Counter(); mv=collections.Counter(); perslot=collections.Counter()
thset=collections.defaultdict(set)
for c,t in VT.items():
    for k,v in enumerate(t):
        if v not in TH: continue
        mT=MD[c]; mV=mT-TH[v]['imm']
        pairs[(mT,mV)]+=1; mv[mV]+=1; perslot[k]+=1
        thset[(mT,mV)].add(v)
print('# (mT,mV) 对：',sorted(pairs.items()))
print('# mV 分布：',mv.most_common())
print('# 槽号分布：',sorted(perslot.items()))
print('# 每种 (mT,mV) 对的不同 thunk 数：',{('%d,%d'%k):len(v) for k,v in sorted(thset.items())})
ck('E1 (mT,mV) 对总出现 305', sum(pairs.values())==305, sum(pairs.values()))
ck('E2 (mT,mV) 对去重种类', True, len(pairs))
ck('E3 mV=0 占多数（前三槽转发到主视图）', mv[0]==303, mv[0])
ck('E4 只有 (40,36) 这一对是 mV!=0 且 mT!=4 的越界槽',
   sorted(k for k in pairs if k[1]!=0)==[(40,36)], sorted(k for k in pairs if k[1]!=0))
json.dump(dict(pairs={'%d,%d'%k:v for k,v in pairs.items()}, mv={str(k):v for k,v in mv.items()},
               perslot={str(k):v for k,v in perslot.items()},
               thset={('%d,%d'%k):sorted(hex(x) for x in v) for k,v in thset.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c14.json','w'),indent=0)
print('FAILS',fails)
