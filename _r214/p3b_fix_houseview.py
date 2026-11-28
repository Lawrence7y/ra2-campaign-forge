# -*- coding: utf-8 -*-
"""R214 p3b：订正 §2.222 第二节 HouseClass 七张视图的地址列表（p3 首版把 COL 地址与 vftable 起点混写）。
实测（a1 C7 + ex2 F4）：视图起点 = COL+? 实际 vftable 起点序列如下。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
F=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
raw=open(F,'rb').read(); assert raw.count(b'\r')==1081
OLD='HouseClass 共 **7** 张视图：`0x8028a0`(mdisp 0, 24 槽) / `0x802918`(4, 6) / `0x802900`(8, 1) / `0x8028e8`(12, 1) / `0x8028d0`(36, 15) / `0x8028b8`(40, 9) / `0x8028a0`(44, 5)。'
NEW='HouseClass 共 **7** 张视图（列 vftable 起点 / COL 记录 / mdisp / 槽数）：`0x7ea8a0`(COL `0x802a28`, 0, **24**) / `0x7ea884`(`0x802918`, 4, **6**) / `0x7ea87c`(`0x802900`, 8, **1**) / `0x7ea874`(`0x8028e8`, 12, **1**) / `0x7ea834`(`0x8028d0`, 36, **15**) / `0x7ea80c`(`0x8028b8`, 40, **9**) / `0x7ea7f4`(`0x8028a0`, 44, **5**)。'
t=raw.decode('utf-8'); assert t.count(OLD)==1,t.count(OLD)
bak=BASE+'/R14_COMMON.md.before_r214_fix_2222_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
assert open(bak,'rb').read()==raw
nb=t.replace(OLD,NEW).encode('utf-8')
open(F,'wb').write(nb); assert open(F,'rb').read()==nb
r=open(F,'rb').read()
assert r.count(b'\r')==1081
print('OK 订正 HouseClass 视图地址：bytes %d -> %d，CR 保持 1081'%(len(raw),len(r)))
