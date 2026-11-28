# -*- coding: utf-8 -*-
"""R210 p2：V592 升版后的指针 / facts_floors / gate_runner 同步重钉（版本目录已由 p1 先写）。
每处写入：wx 独占备份 -> 断言旧值唯一 -> 一次写入 -> 回读 sha 校验。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V592/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
print('V592 sha %s bytes %d lines %d'%(SHA,BYTES,raw.count(b'\n')))
def edit(path,pairs,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r210_%s_20261128.bak'%(tag+'c')
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    for old,new in pairs:
        assert t.count(old)==1,'pattern %r count=%d'%(old[:80],t.count(old))
        t=t.replace(old,new)
    nb=t.encode('utf-8')
    tmp=path+'.r210tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-42s %d -> %d B (cr %d)'%(os.path.basename(path),len(b),len(nb),nb.count(b'\r\n')))

edit(TIER+'/FACT_INDEX_CURRENT.md',[
 ('| 版本目录 | R17_R131_FACTINDEX_V591 |','| 版本目录 | R17_R131_FACTINDEX_V592 |'),
 ('| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V591/FACT_INDEX.tsv |',
  '| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V592/FACT_INDEX.tsv |'),
 ('| sha256 | c529a08cd10e3db4fe8dece6dc9ab3b1d185e96df6f02febaca36682e9c14eed |','| sha256 | %s |'%SHA),
 ('| 字节数 | 245454 |','| 字节数 | %d |'%BYTES),
 ('| 声明轮次 | R209（V591） |','| 声明轮次 | R210（V592） |'),
 ('区间改为 **530..591**。',
  '区间改为 **530..591**；**R210 再升 V592**（律 U：视图偏移集合 = {4} ∪ 本类 QI 正偏移；律 V：thunk 通用式 imm == mT − mV 且落点 == 同类 mV 视图同槽；两律均写入 F29），区间改为 **530..592**。'),
],'ptr592')

FF=ROOT+'/_r160/facts_floors.py'
edit(FF,[
 ("EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V591', 'FACT_INDEX.tsv')",
  "EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V592', 'FACT_INDEX.tsv')"),
 ("CUR_SHA256 = 'c529a08cd10e3db4fe8dece6dc9ab3b1d185e96df6f02febaca36682e9c14eed'",
  "CUR_SHA256 = '%s'"%SHA),
 ('TOTAL_BYTES = 245454','TOTAL_BYTES = %d'%BYTES),
],'ff592')
print('NEXT: p3_master 重算 MASTER_SHA256 + gate_runner LEDGER')
