# -*- coding: utf-8 -*-
"""R213 p3：facts_floors.py 重钉 V596（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER）。"""
import os,hashlib,importlib.util,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
F=ROOT+'/_r160/facts_floors.py'
osha,ob,nsha,nb=open(ROOT+'/_r213/p1_out.txt').read().split(); ob=int(ob); nb=int(nb)
raw=open(F,'rb').read()
fd=os.open(BASE+'/facts_floors.py.before_r213_pin596_20261128.bak',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
os.write(fd,raw); os.close(fd)
assert open(BASE+'/facts_floors.py.before_r213_pin596_20261128.bak','rb').read()==raw
t=raw.decode('utf-8')
for old,new in (("R17_R131_FACTINDEX_V595","R17_R131_FACTINDEX_V596"),
                ("CUR_SHA256 = '%s'"%osha,"CUR_SHA256 = '%s'"%nsha),
                ("TOTAL_BYTES = %d"%ob,"TOTAL_BYTES = %d"%nb)):
    assert t.count(old)==1,(old,t.count(old)); t=t.replace(old,new)
open(F,'wb').write(t.encode('utf-8'))
assert open(F,'rb').read()==t.encode('utf-8')
print('三常量 -> V596')
spec=importlib.util.spec_from_file_location('ff3',F)
m=importlib.util.module_from_spec(spec); sys.argv=['x','--ignore-pin']
spec.loader.exec_module(m)
newmaster=hashlib.sha256(('\n'.join([m.CUR_SHA256,str(m.TOTAL_BYTES),m.canon_g(m.GRADES),m.canon_f(m.FLOORS),
  m.canon_e(m.EVID),m.canon_eb(m.EVIDB),m.canon_l(m.LOST),str(m.ITEMS),str(m.UNIQ),
  str(m.LOST_ITEMS),str(m.LOST_UNIQ)])).encode()).hexdigest()
print('新 MASTER = %s'%newmaster)
s2=open(F,'rb').read().decode('utf-8')
old_m="MASTER_SHA256 = '%s'"%m.MASTER_SHA256
assert s2.count(old_m)==1
open(F,'wb').write(s2.replace(old_m,"MASTER_SHA256 = '%s'"%newmaster).encode('utf-8'))
print('MASTER -> 重钉完成')
