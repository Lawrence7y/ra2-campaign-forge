# -*- coding: utf-8 -*-
"""R218 p2：FACT_INDEX 指针与门禁重钉（先写版本目录、后改指针，顺序不可反）。
改动：facts_floors.py EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER_SHA256；
      gate_runner.py LEDGER 目录；FACT_INDEX_CURRENT.md 指针表 + 声明依据句。
全部为常量替换，FLOORS/GRADES/EVID/EVIDB/LOST 一律不动。
"""
import hashlib,os,re,json
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/R17_LEAD_BASELINE'
os.makedirs(BASE,exist_ok=True)
FF=ROOT+'/_r160/facts_floors.py'
GR=ROOT+'/_r161/gate_runner.py'
PT=TIER+'/FACT_INDEX_CURRENT.md'
NEWD='R17_R131_FACTINDEX_V600'
TSV=TIER+'/'+NEWD+'/FACT_INDEX.tsv'
raw=open(TSV,'rb').read(); newsha=hashlib.sha256(raw).hexdigest()
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def bak(path,tag):
    b=open(path,'rb').read()
    dst='%s/%s.before_r218_%s_20261128.bak'%(BASE,os.path.basename(path),tag)
    if os.path.exists(dst):
        assert open(dst,'rb').read()==b, 'backup differs'
    else:
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
    return b
print('新 V600 sha=%s bytes=%d'%(newsha,len(raw)))
ck('P1 V600 存在且 CR=0', len(raw)>277566 and raw.count(b'\r')==0, (len(raw),raw.count(b'\r')))
# --- 1) facts_floors.py
b0=bak(FF,'FF'); s=b0.decode()
old_exp="EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V599', 'FACT_INDEX.tsv')"
ck('P2 旧 EXPECT_CUR 命中 1 次', s.count(old_exp)==1, s.count(old_exp))
s=s.replace(old_exp,"EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')"%NEWD)
ck('P3 CUR_SHA256 旧值命中 1 次', s.count("CUR_SHA256 = '616a86e251fd88e5d4fa7a3c488c15d65ce2c6e1bceb62de6d639ee1dca374e9'")==1)
s=s.replace("CUR_SHA256 = '616a86e251fd88e5d4fa7a3c488c15d65ce2c6e1bceb62de6d639ee1dca374e9'","CUR_SHA256 = '%s'"%newsha)
ck('P4 TOTAL_BYTES 旧值命中 1 次', s.count('TOTAL_BYTES = 277566')==1)
s=s.replace('TOTAL_BYTES = 277566','TOTAL_BYTES = %d'%len(raw))
open(FF,'wb').write(s.encode())
chk=open(FF,'rb').read().decode()
assert newsha in chk and 'TOTAL_BYTES = %d'%len(raw) in chk and NEWD in chk
print('[FF] 已改 EXPECT_CUR/CUR_SHA256/TOTAL_BYTES')
