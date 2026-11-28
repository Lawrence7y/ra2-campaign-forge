# -*- coding: utf-8 -*-
"""R211 p2：把 EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / LEDGER / MASTER_SHA256 从 V592 重钉到 V593。
MASTER 由 faces_floors 的常量规范化重算（照 R210 p3_master 口径）。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V593/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
OLD_SHA='b3327fd4d89747316b5ad144493de816b1755ff8d279279e90b6d9536ea7371b'; OLD_B=249545
assert SHA.startswith('1f6fe2af'),SHA
print('V593 sha %s bytes %d'%(SHA[:16],BYTES))
def edit(path,pairs,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r211_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    for old,new in pairs:
        assert t.count(old)==1,'pattern %r count=%d'%(old[:90],t.count(old))
        t=t.replace(old,new)
    nb=t.encode('utf-8')
    tmp=path+'.r211tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert open(path,'rb').read()==nb
    print('OK %-22s %d -> %d B'%(os.path.basename(path),len(b),len(nb)))
    return nb
edit(ROOT+'/_r160/facts_floors.py',[
 ("EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V592', 'FACT_INDEX.tsv')",
  "EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V593', 'FACT_INDEX.tsv')"),
 ("CUR_SHA256 = '%s'"%OLD_SHA,"CUR_SHA256 = '%s'"%SHA),
 ('TOTAL_BYTES = %d'%OLD_B,'TOTAL_BYTES = %d'%BYTES),
],"ff")
edit(ROOT+'/_r161/gate_runner.py',[
 ("LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V592', 'FACT_INDEX.tsv')",
  "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V593', 'FACT_INDEX.tsv')"),
],"gr")
# MASTER 重算：跑 p3 逻辑（从 facts_floors 常量规范化）
print('\n--- 运行 facts_floors 取新 MASTER ---')
