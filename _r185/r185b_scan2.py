#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 B：放宽后的虚表 census（槽目标 = .text ∪ .rdata），查 class_ids 69 条覆盖率为何不是 100%。"""
import struct,os,re,json,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
pe=struct.unpack_from('<I',raw,0x3c)[0]
nsec=struct.unpack_from('<H',raw,pe+6)[0]; optsz=struct.unpack_from('<H',raw,pe+20)[0]
opt=pe+24; IB=struct.unpack_from('<I',raw,opt+28)[0]
secs={}
order=[]
for i in range(nsec):
    o=opt+optsz+40*i
    nm=raw[o:o+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',raw,o+8)
    secs[nm]=(va,vs,ra,rs); order.append(nm)
print('secs(va,vsize,rawptr,rawsize)=',{k:(hex(v[0]),hex(v[1]),v[2],v[3]) for k,v in secs.items()})
def r2o(va):
    rva=va-IB
    for nm in order:
        va0,vs,ra,rs=secs[nm]
        if va0<=rva<va0+max(vs,rs): return ra+(rva-va0)
    return None
T=(IB+secs['.text'][0], IB+secs['.text'][0]+secs['.text'][1])
R=(IB+secs['.rdata'][0], IB+secs['.rdata'][0]+secs['.rdata'][1])
print('TEXT',[hex(x) for x in T],'RDATA',[hex(x) for x in R])
# inspect mystery addrs
for a in (0x7FAFC0,0x7FB118,0x7FB160,0x7E1F34,0x7E1F50):
    o=r2o(a)
    ptrs=[]
    for i in range(8):
        v=struct.unpack_from('<I',raw,o+4*i)[0]
        ptrs.append(hex(v))
    print('AT',hex(a),'sec rdata?',R[0]<=a<R[1],ptrs)
