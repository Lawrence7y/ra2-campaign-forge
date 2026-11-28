# -*- coding: utf-8 -*-
"""R218 m5：实测 BaseClassDescriptor 数组真实布局（m4 的「自身 BCD」判据失败，需先钉布局）。
对 UnitClass COL 0x80cc80 / BuildingClass COL 0x7fc298：
 打印 COL 全字段、CHD 全字段、pBaseArray 前 8 个 dword、每个元素地址处 0x1c 字节 hexdump 与逐字段解码。
正控：ncb 序列应单调递减 15,14,13...（m3/m4 已见）。
"""
import sys,struct
sys.path.insert(0,'_r185'); import pe185 as P
def dw(a):
    o=P.r2o(a); return None if o is None else struct.unpack_from('<I',P.RAW,o)[0]
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def dump(a,n):
    o=P.r2o(a); return P.RAW[o:o+n].hex() if o is not None else None
def cstr(a,m=256):
    r=P.cstr(a,m); return r.decode('latin1') if r else None
for col in (0x80cc80,0x7fc298,0x7fb0c8):
    print('='*100)
    print('COL %08x  raw=%s'%(col,dump(col,24)))
    print('  +0 sig=%d +4 mdisp=%d +8 pCD=%08x +c pTD=%08x +10 pCHD=%08x +14 self=%08x'%(
        dw(col),s32(dw(col+4)),dw(col+8),dw(col+0xc),dw(col+0x10),dw(col+0x14)))
    td=dw(col+0xc); chd=dw(col+0x10)
    print('  TD %08x name=%s  TD+0=%08x (+8 名为本类)'%(td,cstr(td+8),dw(td)))
    print('  CHD %08x raw=%s'%(chd,dump(chd,16)))
    print('    +0 sig=%d +4 attrs=%08x +8 numBase=%d +c pBaseArray=%08x'%(dw(chd),dw(chd+4),dw(chd+8),dw(chd+0xc)))
    arr=dw(chd+0xc); nb=dw(chd+8)
    print('  pBaseArray %08x 前 8 dword: %s'%(arr,[hex(dw(arr+4*i)) for i in range(8)]))
    print('  数组原始 32 字节: %s'%dump(arr,32))
    for i in range(min(nb,4)):
        e=dw(arr+4*i)
        print('   --- 元素[%d] 值 %08x 处 0x1c 字节: %s'%(i,e,dump(e,0x1c)))
        print('       +0 pTD=%08x(%s) +4 ncb=%d +8 mdisp=%d +c pdisp=%d +10 vdisp=%d +14 attrs=%08x +18 p=%08x'%(
            dw(e),cstr(dw(e)+8),dw(e+4),s32(dw(e+8)),s32(dw(e+0xc)),s32(dw(e+0x10)),dw(e+0x14),dw(e+0x18)))
