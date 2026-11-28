# -*- coding: utf-8 -*-
"""R215 p3b：facts_floors.py 的 MASTER_SHA256 重钉（三常量已由 p3 首次运行改好）。"""
import os,hashlib,importlib.util,sys,io,contextlib
ROOT='/home/t628/projects/ra2-campaign-forge'
F=ROOT+'/_r160/facts_floors.py'
s0=open(F,'rb').read().decode('utf-8')
buf=io.StringIO()
spec=importlib.util.spec_from_file_location('ff5',F)
m=importlib.util.module_from_spec(spec); sys.argv=['x','--ignore-pin']
with contextlib.redirect_stdout(buf):
    spec.loader.exec_module(m)
newmaster=hashlib.sha256(('\n'.join([m.CUR_SHA256,str(m.TOTAL_BYTES),m.canon_g(m.GRADES),m.canon_f(m.FLOORS),
  m.canon_e(m.EVID),m.canon_eb(m.EVIDB),m.canon_l(m.LOST),str(m.ITEMS),str(m.UNIQ),
  str(m.LOST_ITEMS),str(m.LOST_UNIQ)])).encode()).hexdigest()
old="MASTER_SHA256 = '%s'"%m.MASTER_SHA256
print('旧 %s -> 新 %s'%(m.MASTER_SHA256[:12],newmaster[:12]))
assert s0.count(old)==1,s0.count(old)
open(F,'wb').write(s0.replace(old,"MASTER_SHA256 = '%s'"%newmaster).encode('utf-8'))
assert "MASTER_SHA256 = '%s'"%newmaster in open(F,'rb').read().decode('utf-8')
print('已重钉')
