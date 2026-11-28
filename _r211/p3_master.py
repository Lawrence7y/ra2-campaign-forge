# -*- coding: utf-8 -*-
"""R211 p3：重钉 MASTER_SHA256 到新值 ae756204...（facts_floors 自算得出）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
F=ROOT+'/_r160/facts_floors.py'
OLD='519ee33aa283a7f7f3abebad0a9a9369b6fe45e24a8d4f080faf2fe832cb9d43'
NEW='ae7562048fe94555dbdf0ab75fbe6928d61c874ee0d5f0d2722a64d6027eb6e1'
b=open(F,'rb').read()
bak=BASE+'/facts_floors.py.before_r211_master_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b
t=b.decode('utf-8')
assert t.count(OLD)==1,t.count(OLD)
t=t.replace(OLD,NEW)
nb=t.encode('utf-8')
tmp=F+'.r211tmp'; open(tmp,'wb').write(nb); os.replace(tmp,F)
assert open(F,'rb').read()==nb
print('MASTER repinned %s -> %s'%(OLD[:16],NEW[:16]))
