# -*- coding: utf-8 -*-
"""R215 p3c：计算并重钉 facts_floors MASTER_SHA256（在 exec 前把 sys.exit 打成 no-op）。"""
import os,hashlib,io,contextlib,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
F=ROOT+'/_r160/facts_floors.py'
s0=open(F,'rb').read().decode('utf-8')
class NoExit(Exception): pass
orig=sys.exit
def fake(code=0): raise NoExit(code)
ns={'__file__':F,'__name__':'ff','__builtins__':__builtins__}
sys.exit=fake
buf=io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        exec(compile(s0,F,'exec'),ns)
except NoExit:
    pass
finally:
    sys.exit=orig
newmaster=hashlib.sha256(('\n'.join([ns['CUR_SHA256'],str(ns['TOTAL_BYTES']),ns['canon_g'](ns['GRADES']),
  ns['canon_f'](ns['FLOORS']),ns['canon_e'](ns['EVID']),ns['canon_eb'](ns['EVIDB']),
  ns['canon_l'](ns['LOST']),str(ns['ITEMS']),str(ns['UNIQ']),str(ns['LOST_ITEMS']),str(ns['LOST_UNIQ'])])).encode()).hexdigest()
old=ns['MASTER_SHA256']
print('旧 %s -> 新 %s'%(old[:12],newmaster[:12]))
assert s0.count("MASTER_SHA256 = '%s'"%old)==1
open(F,'wb').write(s0.replace("MASTER_SHA256 = '%s'"%old,"MASTER_SHA256 = '%s'"%newmaster).encode('utf-8'))
assert ("MASTER_SHA256 = '%s'"%newmaster) in open(F,'rb').read().decode('utf-8')
print('已重钉')
