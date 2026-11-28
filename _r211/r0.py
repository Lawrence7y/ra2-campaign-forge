# -*- coding: utf-8 -*-
"""R211 r0 基础：从 q3.json 重建 954 类 / 视图偏移集合，取 {4} 独立附加项 8 类名单。
只读，不写盘。"""
import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
print('views=%d'%len(VT))
cls=collections.defaultdict(dict)
for v in MD: cls[P.dw(v+16)][MD[v]]=v
print('classes=%d  with main(mdisp=0)=%d'%(len(cls),sum(1 for c in cls if 0 in cls[c])))
# 8 classes: mdisp views = {4} only (no 0) and R({24} etc.) independent
eight=[]
for c,vs in cls.items():
    if 0 in vs: continue
    offs=sorted(vs)
    eight.append((hex(c),NM.get(vs[offs[0]],'?'),offs,[hex(vs[o]) for o in offs]))
print('无 mdisp=0 视图的类 = %d'%len(eight))
for e in sorted(eight,key=lambda x:x[2]): print('  ',e)
