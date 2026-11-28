# -*- coding: utf-8 -*-
"""R211 c4：实证 CHD/BCA/BCD 字段口径（c3 得 B 全空因 lookup 用错表）。
CHD=0x802a18（HouseClass）：+0 sig / +4 attrs / +8 numBaseClasses / +12 pBCA。
BCA 元素是 BCD 记录地址（R207 订正）。逐条打印 24B 记录六字段。"""
import sys
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import struct
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
chd=0x802a18
print('CHD %#x: sig=%d attrs=%d n=%d pBCA=%#x'%(chd,P.dw(chd),P.dw(chd+4),P.dw(chd+8),P.dw(chd+12)))
pbca=P.dw(chd+12); n=P.dw(chd+8)
for j in range(n):
    b=P.dw(pbca+4*j)
    f=[P.dw(b+4*z) for z in range(6)]
    nm=P.cstr(f[4]+8,300) if P.where(f[4])=='.data' else None
    print('  [%2d] BCD=%#010x  pdisp=%d vdisp=%d mdisp=%d nc=%d pTD=%#x %s'%(
        j,b,s32(f[0]),s32(f[1]),s32(f[2]),f[3],f[4],nm))
