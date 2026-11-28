# -*- coding: utf-8 -*-
"""R212 p2：facts_floors.py 重钉 V594（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES）+ MASTER 重算。
纪律：wx 备份 + 旧值断言 + 逐处唯一替换 + 回读 + 自检 master。
"""
import os,hashlib,re,importlib.util,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
F=ROOT+'/_r160/facts_floors.py'
osha,ob,nsha,nb=open(ROOT+'/_r212/p1_out.txt').read().split()
ob=int(ob); nb=int(nb)
raw=open(F,'rb').read()
fd=os.open(BASE+'/facts_floors.py.before_r212_pin594_20261128.bak',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
os.write(fd,raw); os.close(fd)
t=raw.decode('utf-8'); ORIG=t
reps=[("R17_R131_FACTINDEX_V593","R17_R131_FACTINDEX_V594"),
      ("CUR_SHA256 = '%s'"%osha,"CUR_SHA256 = '%s'"%nsha),
      ("TOTAL_BYTES = %d"%ob,"TOTAL_BYTES = %d"%nb)]
for old,new in reps:
    assert t.count(old)==1,(old,t.count(old))
    t=t.replace(old,new)
open(F,'wb').write(t.encode('utf-8'))
assert open(F,'rb').read()==t.encode('utf-8')
print('三处常量已重钉 -> V594')
# 自检：导入模块（带 --ignore-pin 不行，故手动算 master）
spec=importlib.util.spec_from_file_location('ff',F)
m=importlib.util.module_from_spec(spec)
sys.argv=['x','--ignore-pin']
spec.loader.exec_module(m)
newmaster=hashlib.sha256(('\n'.join([m.CUR_SHA256,str(m.TOTAL_BYTES),m.canon_g(m.GRADES),m.canon_f(m.FLOORS),
  m.canon_e(m.EVID),m.canon_eb(m.EVIDB),m.canon_l(m.LOST),str(m.ITEMS),str(m.UNIQ),
  str(m.LOST_ITEMS),str(m.LOST_UNIQ)])).encode()).hexdigest()
print('新 MASTER = %s'%newmaster)
print('原 MASTER = %s'%m.MASTER_SHA256)
raw2=open(F,'rb').read().decode('utf-8')
assert raw2.count(m.MASTER_SHA256)==1
new2=raw2.replace(m.MASTER_SHA256,newmaster)
open(F,'wb').write(new2.encode('utf-8'))
print('MASTER 已重钉')
open(ROOT+'/_r212/p2_out.txt','w').write('%s %s\n'%(newmaster,nsha))
