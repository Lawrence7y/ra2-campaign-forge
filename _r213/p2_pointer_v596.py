# -*- coding: utf-8 -*-
"""R213 p2：FACT_INDEX_CURRENT.md 指针 V595 -> V596（wx 备份 + 断言 + 回读）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
PTR=TIER+'/FACT_INDEX_CURRENT.md'
OSHA,OB,NSHA,NB=open(ROOT+'/_r213/p1_out.txt').read().split(); OB=int(OB); NB=int(NB)
b=open(PTR,'rb').read()
assert hashlib.sha256(b).hexdigest() and b.count(OSHA.encode())>=1,b'pointer sha mismatch'
bak=BASE+'/FACT_INDEX_CURRENT.md.before_r213_ptr596_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b
t=b.decode('utf-8')
for old,new in (('| sha256 | %s |'%OSHA,'| sha256 | %s |'%NSHA),
                ('| 字节数 | %d |'%OB,'| 字节数 | %d |'%NB)):
    assert t.count(old)==1,(old,t.count(old)); t=t.replace(old,new)
assert t.count('V595')>=2,t.count('V595')
t2=t.replace('R17_R131_FACTINDEX_V595','R17_R131_FACTINDEX_V596').replace('V595','V596')
t2=t2.replace('| 声明轮次 | R210（V596） |','| 声明轮次 | R213（V596） |')
t2=t2.replace('**R210 再升 V596**','**R213 再升 V596**')
open(PTR,'wb').write(t2.encode('utf-8'))
assert open(PTR,'rb').read()==t2.encode('utf-8')
print('PTR -> V596 ; 行数 %d'%t2.count('\n'))
print('sha in pointer:',NSHA[:16],'bytes',NB)
