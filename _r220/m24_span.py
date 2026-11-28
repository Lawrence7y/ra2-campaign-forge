# -*- coding: utf-8 -*-
"""R220 m24：定 0x87b170 / 0x876ff4 表的真实跨度与块结构。"""
import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
def analyze(va,name,maxrec=400):
    o=P.r2o(va); rows=[]
    for i in range(maxrec):
        r=list(struct.unpack_from('<8H',R,o+i*16))
        rows.append(r)
    print("=== %s @%#x"%(name,va))
    for i in range(0,20):
        r=rows[i]; print("  rec%-3d a=%-5d d=%s"%(i,r[0],tuple(r[j]-r[0] for j in range(8))))
    print("  ... rec160-165:")
    for i in range(160,166):
        r=rows[i]; print("  rec%-3d a=%-5d d=%s"%(i,r[0],tuple(r[j]-r[0] for j in range(8))))
    # 判定「记录型」= 前4字相等 且 后4字严格递增且差值恒定于本记录
    ok=0
    for i in range(maxrec):
        r=rows[i]
        if not (r[0]==r[1]==r[2]==r[3]): break
        d=[r[j+1]-r[j] for j in range(4,7)]
        if len(set(d))!=1: break
        ok+=1
    print("  记录型连续段长度 =",ok," 字节 =",ok*16)
    # 后半是否也是记录型（不同 delta）
    return rows,ok
rA,okA=analyze(0x876ff4,'A表')
rB,okB=analyze(0x87b170,'B表')
# 96 字节周期检测：0x87b170 起是否 96B 重复
o=P.r2o(0x87b170)
per96=0
for i in range(1,400):
    if R[o:o+96]==R[o+96*(i):o+96*(i+1)]: per96+=1
    else: break
print("96B 周期重复段数 =",per96,"bytes=",per96*96)
# 结构注释打印前 96*4 字节
print("前 4 个 96B 块:")
for b in range(4):
    print("  ",P.RAW[o+96*b:o+96*b+96].hex())
