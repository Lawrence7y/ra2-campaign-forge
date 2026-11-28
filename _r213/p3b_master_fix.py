# -*- coding: utf-8 -*-
"""R213 p3b：修正 MASTER 重钉（上一版 p3 因 facts_floors.py 末尾 sys.exit 提前终止，MASTER 未写）。
用 try/except SystemExit 包住 exec_module，再取常量重算。"""
import os,hashlib,importlib.util,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
F=ROOT+'/_r160/facts_floors.py'
raw=open(F,'rb').read()
print('before MASTER =', [l for l in raw.decode().split('\n') if l.startswith('MASTER_SHA256')])
spec=importlib.util.spec_from_file_location('ff5',F)
m=importlib.util.module_from_spec(spec); sys.argv=['x','--ignore-pin']
try:
    spec.loader.exec_module(m)
except SystemExit as e:
    print('module exited with',e.code,'(constants already bound)')
new=hashlib.sha256(('\n'.join([m.CUR_SHA256,str(m.TOTAL_BYTES),m.canon_g(m.GRADES),m.canon_f(m.FLOORS),
  m.canon_e(m.EVID),m.canon_eb(m.EVIDB),m.canon_l(m.LOST),str(m.ITEMS),str(m.UNIQ),
  str(m.LOST_ITEMS),str(m.LOST_UNIQ)])).encode()).hexdigest()
print('pinned %s  recomputed %s'%(m.MASTER_SHA256[:16],new[:16]))
assert new!=m.MASTER_SHA256
bak=BASE+'/facts_floors.py.before_r213_master2_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
t=raw.decode('utf-8'); old="MASTER_SHA256 = '%s'"%m.MASTER_SHA256
assert t.count(old)==1,t.count(old)
nb=t.replace(old,"MASTER_SHA256 = '%s'"%new).encode('utf-8')
open(F,'wb').write(nb); assert open(F,'rb').read()==nb
print('written; MASTER -> %s'%new)
