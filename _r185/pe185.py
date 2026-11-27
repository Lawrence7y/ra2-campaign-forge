# -*- coding: utf-8 -*-
"""R185 公共 PE 映射（从 PE 头动态推导，不硬编码边界）。"""
import struct
ROOT='/home/t628/projects/ra2-campaign-forge'
RAW=open(ROOT+'/ra2bench/gamemd.exe','rb').read()
pe=struct.unpack_from('<I',RAW,0x3c)[0]
assert RAW[pe:pe+4]==b'PE\0\0'
NSEC=struct.unpack_from('<H',RAW,pe+6)[0]
OPTSZ=struct.unpack_from('<H',RAW,pe+20)[0]
IB=struct.unpack_from('<I',RAW,pe+24+28)[0]
SECS=[]
for i in range(NSEC):
    o=pe+24+OPTSZ+40*i
    nm=RAW[o:o+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',RAW,o+8)
    SECS.append({'name':nm,'va':IB+va,'vsize':vs,'rawptr':ra,'rawsize':rs,
                 'lo':IB+va,'hi_file':IB+va+rs,'hi_virt':IB+va+vs})
B={s['name']:s for s in SECS}
def sec_of(va):
    for s in SECS:
        if s['lo']<=va<s['hi_file']: return s['name']
    return None
def r2o(va):
    for s in SECS:
        if s['lo']<=va<s['hi_file']: return s['rawptr']+(va-s['lo'])
    return None
def dw(va):
    o=r2o(va)
    return None if o is None else struct.unpack_from('<I',RAW,o)[0]
def where(va):
    if va is None: return 'None'
    s=sec_of(va)
    return s if s else ('virt-only' if any(x['lo']<=va<x['hi_virt'] for x in SECS) else 'other')
def cstr(va,m=300):
    o=r2o(va)
    if o is None: return None
    e=RAW.find(b'\0',o,o+m)
    return None if e<0 else RAW[o:e]
