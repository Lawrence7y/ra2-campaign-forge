# -*- coding: utf-8 -*-
"""R210 p2b：把已指向 V592 目录的指针/facts_floors/gate_runner 更新为 V592 的**最终** sha 与字节数
（p1 期间因律 U 收紧而重写过一次，旧值 735a7b5b/249150 已过期，必须同步）。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V592/FACT_INDEX.tsv'
raw=open(NEW,'rb').read(); SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
OLD_SHA='735a7b5be70d093cf91bb9795662985ad184bcb1483e15851920ed14de78e5d8'; OLD_B=249150
assert SHA!=OLD_SHA
print('V592 final sha %s bytes %d'%(SHA,BYTES))
def edit(path,pairs,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r210_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    for old,new in pairs:
        assert t.count(old)==1,'pattern %r count=%d'%(old[:80],t.count(old))
        t=t.replace(old,new)
    nb=t.encode('utf-8')
    tmp=path+'.r210tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-30s %d -> %d B (cr %d)'%(os.path.basename(path),len(b),len(nb),nb.count(b'\r\n')))
edit(TIER+'/FACT_INDEX_CURRENT.md',[
 ('| sha256 | %s |'%OLD_SHA,'| sha256 | %s |'%SHA),
 ('| 字节数 | %d |'%OLD_B,'| 字节数 | %d |'%BYTES),
],'ptrb')
edit(ROOT+'/_r160/facts_floors.py',[
 ("CUR_SHA256 = '%s'"%OLD_SHA,"CUR_SHA256 = '%s'"%SHA),
 ('TOTAL_BYTES = %d'%OLD_B,'TOTAL_BYTES = %d'%BYTES),
],'ffb')
