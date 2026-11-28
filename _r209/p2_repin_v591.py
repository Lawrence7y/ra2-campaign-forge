# -*- coding: utf-8 -*-
"""R209 p2：V591 升版后的指针/facts_floors/gate_runner 同步重钉（版本目录已在 p1 先写）。
每处写入：wx 独占备份 -> 断言旧值唯一 -> 一次写入 -> 回读 sha 校验。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V591/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
print('V591 sha %s bytes %d lines %d'%(SHA,BYTES,raw.count(b'\n')))
def edit(path,pairs,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r209_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    for old,new in pairs:
        assert t.count(old)==1,'pattern %r count=%d'%(old[:70],t.count(old))
        t=t.replace(old,new)
    nb=t.encode('utf-8')
    tmp=path+'.r209tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-42s %d -> %d B (cr %d)'%(os.path.basename(path),len(b),len(nb),nb.count(b'\r\n')))
edit(TIER+'/FACT_INDEX_CURRENT.md',[
 ('| 版本目录 | R17_R131_FACTINDEX_V590 |','| 版本目录 | R17_R131_FACTINDEX_V591 |'),
 ('| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V590/FACT_INDEX.tsv |',
  '| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V591/FACT_INDEX.tsv |'),
 ('| sha256 | e49a3eddc47d7cc5183d6aa9f103a2a0f7e1ee679379763b5aa6ef5866c6ec33 |','| sha256 | %s |'%SHA),
 ('| 字节数 | 242630 |','| 字节数 | %d |'%BYTES),
 ('| 声明轮次 | R208（V590） |','| 声明轮次 | R209（V591） |'),
 ('区间改为 **530..590**。','区间改为 **530..590**；**R209 再升 V591**（律 T 由「slot0 一条」扩展为「IUnknown 三槽三连」并写入 F29），区间改为 **530..591**。'),
],'ptr591')
FF=ROOT+'/_r160/facts_floors.py'
edit(FF,[
 ("EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V590', 'FACT_INDEX.tsv')",
  "EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V591', 'FACT_INDEX.tsv')"),
 ("CUR_SHA256 = 'e49a3eddc47d7cc5183d6aa9f103a2a0f7e1ee679379763b5aa6ef5866c6ec33'","CUR_SHA256 = '%s'"%SHA),
 ('TOTAL_BYTES = 242630','TOTAL_BYTES = %d'%BYTES),
],'ff591')
print('DONE (MASTER_SHA256 与 gate_runner 由 p3 处理)')
