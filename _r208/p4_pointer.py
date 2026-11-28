# -*- coding: utf-8 -*-
"""R208 p4：升版指针 + facts_floors 常量 + gate_runner LEDGER（顺序：新版本目录已先写）。
每处写入均 wx 备份 -> 断言旧 sha -> 一次性写 -> 回读校验。
"""
import os,re,hashlib,json,io,subprocess,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
NEW=TIER+'/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv'
raw=open(NEW,'rb').read()
SHA=hashlib.sha256(raw).hexdigest(); BYTES=len(raw)
NROWS=raw.count(b'\n')
print('V589 sha',SHA[:16],'bytes',BYTES,'lines',NROWS)

def edit(path, pairs, tag):
    b=open(path,'rb').read()
    s0=hashlib.sha256(b).hexdigest()
    bak=BASE+'/'+os.path.basename(path)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    t=b.decode('utf-8')
    for old,new in pairs:
        assert t.count(old)==1, 'pattern not unique: %r (%d)'%(old[:60],t.count(old))
        t=t.replace(old,new)
    nb=t.encode('utf-8')
    tmp=path+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest()
    print('OK %-46s %d -> %d B (bak %s)'%(os.path.basename(path),len(b),len(nb),os.path.basename(bak)))
    return len(nb)

# 1) 指针（先写版本目录、后改指针，顺序正确）
PTR=TIER+'/FACT_INDEX_CURRENT.md'
edit(PTR,[
 ('| 版本目录 | R17_R131_FACTINDEX_V588 |','| 版本目录 | R17_R131_FACTINDEX_V589 |'),
 ('| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V588/FACT_INDEX.tsv |',
  '| 相对路径 | lead/next_re_20261117_r14/R17_R131_FACTINDEX_V589/FACT_INDEX.tsv |'),
 ('| sha256 | bfad05b0a5d95dbc9e9862d15fdd43f0427f02c276476319a2760b5835bc20b4 |',
  '| sha256 | %s |'%SHA),
 ('| 字节数 | 239742 |','| 字节数 | %d |'%BYTES),
 ('| 声明轮次 | R205 |','| 声明轮次 | R208 |'),
],'ptr')
