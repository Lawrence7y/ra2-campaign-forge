# -*- coding: utf-8 -*-
"""R216 p1b：把 V599 接入事实层 —— 改 facts_floors 的 CUR 常量（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES）
与 FLOORS['F29'].stmt、MASTER_SHA256；改 gate_runner 的 LEDGER 路径；改 check_disc 的 C16_FLOORS 223 节。
写入纪律：每处改前 wx 独占备份（R17_LEAD_BASELINE）+ 断言旧 sha/sha 命中次数 == 1 + 改后回读校验。"""
import os,hashlib,sys,io,contextlib,json,re
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
os.makedirs(BASE,exist_ok=True)
d=json.load(open(ROOT+'/_r216/p1.json'))
NEWSHA=d['new_sha']; NEWBYTES=d['new_bytes']; NEWF29B=d['stmt_bytes']
def backup(path,tag):
    b=open(path,'rb').read()
    h=hashlib.sha256(b).hexdigest()
    dst=BASE+'/%s.before_r216_%s_20261128.bak'%(os.path.basename(path),tag)
    assert not os.path.exists(dst), 'BACKUP EXISTS '+dst
    open(dst,'wb').write(b)
    return b,h
def write(path,b,expect_sha,expect_cnt=1,oldstr=None):
    s=b.decode('utf-8'); assert hashlib.sha256(b).hexdigest()==expect_sha
    return s
# ---------- facts_floors ----------
FF=ROOT+'/_r160/facts_floors.py'
b0,h0=backup(FF,'r216')
s0=b0.decode('utf-8')
print('facts_floors 旧 sha=%s'%h0[:16])
assert s0.count("CUR_SHA256 = '45d366aee41bec2e876324e8d281e15440b6101a800d1635e007d798b37539f5'")==1
s1=s0.replace("CUR_SHA256 = '45d366aee41bec2e876324e8d281e15440b6101a800d1635e007d798b37539f5'",
              "CUR_SHA256 = '%s'"%NEWSHA)
assert s1.count("TOTAL_BYTES = 275368")==1
s2=s1.replace("TOTAL_BYTES = 275368","TOTAL_BYTES = %d"%NEWBYTES)
assert s2.count("R17_R131_FACTINDEX_V598")==1, s2.count("R17_R131_FACTINDEX_V598")
s3=s2.replace("R17_R131_FACTINDEX_V598","R17_R131_FACTINDEX_V599")
assert s3.count("'F29': (3435, 20898),")==1
s4=s3.replace("'F29': (3435, 20898),","'F29': (3435, %d),"%NEWF29B)
assert s4!=s3
open(FF,'wb').write(s4.encode('utf-8'))
open(ROOT+'/_r216/p1b_ff1.py','w').write(s4)
print('facts_floors CUR/TOTAL/HINT/F29 已改（MASTER 待重算）')
# ---------- 重算 MASTER ----------
old_exit=sys.exit
class NX(Exception): pass
sys.exit=lambda c=0:(_ for _ in ()).throw(NX(c))
ns={'__file__':FF,'__name__':'ff','__builtins__':__builtins__}
buf=io.StringIO()
try:
    with contextlib.redirect_stdout(buf): exec(compile(s4,FF,'exec'),ns)
except NX: pass
finally: sys.exit=old_exit
newm=hashlib.sha256(('\n'.join([ns['CUR_SHA256'],str(ns['TOTAL_BYTES']),ns['canon_g'](ns['GRADES']),
  ns['canon_f'](ns['FLOORS']),ns['canon_e'](ns['EVID']),ns['canon_eb'](ns['EVIDB']),
  ns['canon_l'](ns['LOST']),str(ns['ITEMS']),str(ns['UNIQ']),str(ns['LOST_ITEMS']),str(ns['LOST_UNIQ'])])).encode()).hexdigest()
oldm=ns['MASTER_SHA256']
print('MASTER %s -> %s'%(oldm[:16],newm[:16]))
assert s4.count("MASTER_SHA256 = '%s'"%oldm)==1
s5=s4.replace("MASTER_SHA256 = '%s'"%oldm,"MASTER_SHA256 = '%s'"%newm)
open(FF,'wb').write(s5.encode('utf-8'))
assert hashlib.sha256(open(FF,'rb').read()).hexdigest()==hashlib.sha256(s5.encode()).hexdigest()
print('facts_floors 写入并回读一致 sha=%s'%hashlib.sha256(open(FF,'rb').read()).hexdigest()[:16])
# ---------- gate_runner ----------
GR=ROOT+'/_r161/gate_runner.py'
b1,h1=backup(GR,'r216'); t0=b1.decode('utf-8')
assert t0.count("R17_R131_FACTINDEX_V598")==1
t1=t0.replace("R17_R131_FACTINDEX_V598","R17_R131_FACTINDEX_V599")
open(GR,'wb').write(t1.encode('utf-8'))
assert "V599" in open(GR,'rb').read().decode('utf-8')
print('gate_runner LEDGER -> V599 (旧 sha=%s)'%h1[:16])
json.dump({'ff_old':h0,'ff_new':hashlib.sha256(open(FF,'rb').read()).hexdigest(),
 'gr_old':h1,'gr_new':hashlib.sha256(open(GR,'rb').read()).hexdigest(),
 'master_old':oldm,'master_new':newm,'new_sha':NEWSHA,'new_bytes':NEWBYTES,'f29b':NEWF29B},
 open(ROOT+'/_r216/p1b.json','w'),indent=1)
