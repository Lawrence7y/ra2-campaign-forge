# -*- coding: utf-8 -*-
"""R216 p2：改 FACT_INDEX_CURRENT.md 指针（顺序：先写好 V599 目录，再改指针；p1 已完成目录）。"""
import os,hashlib,json,re
ROOT='/home/t628/projects/ra2-campaign-forge'; T=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
d=json.load(open(ROOT+'/_r216/p1.json'))
F=T+'/FACT_INDEX_CURRENT.md'
b0=open(F,'rb').read(); h0=hashlib.sha256(b0).hexdigest(); s0=b0.decode('utf-8')
dst=BASE+'/FACT_INDEX_CURRENT.md.before_r216_ptr599_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
print('指针旧 sha=%s bytes=%d'%(h0[:16],len(b0)))
assert s0.count('R17_R131_FACTINDEX_V598')==2
s1=s0.replace('R17_R131_FACTINDEX_V598','R17_R131_FACTINDEX_V599')
assert s1.count('45d366aee41bec2e876324e8d281e15440b6101a800d1635e007d798b37539f5')==1
s2=s1.replace('45d366aee41bec2e876324e8d281e15440b6101a800d1635e007d798b37539f5',d['new_sha'])
assert s2.count('| 275368 |')==1
s3=s2.replace('| 275368 |','| %d |'%d['new_bytes'])
assert s3.count('| 声明轮次 | R215（V598） |')==1
s4=s3.replace('| 声明轮次 | R215（V598） |','| 声明轮次 | R216（V599） |')
assert s4.count('区间改为 **530..598**')==1
s5=s4.replace('区间改为 **530..598**','区间改为 **530..599**')
# 追加 R216 说明（在声明依据末尾、表格行内）
old_tail='**R215 再升 V598**'
i=s5.index(old_tail); j=s5.index('\n',i)
ins=(' **R216 再升 V599**（?AVAbstractClass@@ 四子对象 MI 布局实证 + 四个 IID 常量 + 律 U 101/101 + 律 W 违例 360 条全为正偏移，并入 F29），区间改为 **530..599**。')
s6=s5[:j]+ins+s5[j:]
open(F,'wb').write(s6.encode('utf-8'))
r=open(F,'rb').read()
print('指针新 sha=%s bytes=%d'%(hashlib.sha256(r).hexdigest()[:16],len(r)))
assert d['new_sha'] in r.decode(); assert 'R216（V599）' in r.decode()
json.dump({'ptr_old':h0,'ptr_new':hashlib.sha256(r).hexdigest(),'ptr_old_bytes':len(b0),'ptr_new_bytes':len(r)},
 open(ROOT+'/_r216/p2.json','w'),indent=1)
