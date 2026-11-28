# -*- coding: utf-8 -*-
"""R215 p2：FACT_INDEX_CURRENT.md 指针 V597 -> V598（wx 备份 + 断言 + 回读）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
PTR=TIER+'/FACT_INDEX_CURRENT.md'
OSHA,OB,NSHA,NB=open(ROOT+'/_r215/p1_out.txt').read().split(); OB=int(OB); NB=int(NB)
b=open(PTR,'rb').read()
assert OSHA.encode() in b, b'pointer sha mismatch'
bak=BASE+'/FACT_INDEX_CURRENT.md.before_r215_ptr598_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b
t=b.decode('utf-8')
for old,new in (('| sha256 | %s |'%OSHA,'| sha256 | %s |'%NSHA),
                ('| 字节数 | %d |'%OB,'| 字节数 | %d |'%NB)):
    assert t.count(old)==1,(old,t.count(old)); t=t.replace(old,new)
assert t.count('V597')>=2,t.count('V597')
t2=t.replace('R17_R131_FACTINDEX_V597','R17_R131_FACTINDEX_V598').replace('V597','V598')
t2=t2.replace('| 声明轮次 | R214（V598） |','| 声明轮次 | R215（V598） |')
t2=t2.replace('**R214 再升 V598**','**R215 再升 V598**（虚槽 +0x48 落点归因：27 落点 = 9 多类组 + 18 单类组，'
              '0x4104c0 为基类 12 字节描述符取值器，配套 931 处 +0x48 消费位点归并为 273 函数；'
              '口径订正：305 双口径同值巧合、adjustor distinct 桩 70、Locomotion 11+1、三全局 virt-only），区间改为 **530..598**。')
open(PTR,'wb').write(t2.encode('utf-8'))
assert open(PTR,'rb').read()==t2.encode('utf-8')
print('PTR -> V598 ; 行数 %d'%t2.count('\n'))
print('sha in pointer:',NSHA[:16],'bytes',NB)
