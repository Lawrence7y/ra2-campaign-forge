#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106a2_probe.py —— 第二轮探测：重复项值的目标块是否依赖索引寄存器 + default 块复用"""
import struct, sys, os
ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, '_r104/vendor')
import iced_x86
F = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)
raw = open('ra2bench/gamemd.exe', 'rb').read()
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6); osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24; IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))
def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs): return ra + (r - srva)
def u32(va): return struct.unpack_from('<I', raw, off(va))[0]
def dis_at(va, n=1):
    o = off(va); dec = iced_x86.Decoder(32, raw[o:o + 15 * n + 32], ip=va)
    return [dec.decode() for _ in range(n) if dec.can_decode]

ROWS = [
 (0x46f5a0,4,0x46e4be,47,0x46f5b0,True,0x46f4c9,'ecx'),
 (0x48db10,13,0x48d583,37,0x48db44,True,0x48dac4,'edx'),
 (0x48dd10,5,0x48dce0,39,0x48dd24,True,0x48dd0d,'ecx'),
 (0x4c8114,46,0x4c6cd7,45,None,False,0x4c8109,None),
 (0x5001e4,5,0x4ffde9,4,None,False,0x5001ce,None),
 (0x58bda4,5,0x58bd85,4,None,False,0x58bda1,None),
 (0x69b15c,4,0x69af3e,3,None,False,0x69b148,None),
 (0x6a92c4,3,0x6a8e1e,14,0x6a92d0,True,0x6a8f49,'ecx'),
 (0x6adbdc,3,0x6acf2a,22,0x6adbe8,True,0x6adbcc,'ecx'),
 (0x6b0238,7,0x6afd73,6,None,False,0x6b0231,None),
 (0x6dfdec,145,0x6dd8e7,144,None,False,0x6dfddd,None),
 (0x708d54,5,0x708c4e,4,None,False,0x708d4d,None),
 (0x71f2c0,14,0x71eea2,45,0x71f2f8,True,0x71f069,'edx'),
 (0x71f328,10,0x71f092,55,0x71f350,True,0x71f1b1,'ecx'),
 (0x71f778,2,0x71f6d0,55,0x71f780,True,0x71f6da,'eax'),
 (0x71f9e0,2,0x71f9d3,58,0x71f9e8,True,0x71f9dd,'ecx'),
 (0x728e08,7,0x728c17,6,None,False,0x728dfc,'eax'),
 (0x7291ac,7,0x728e6c,6,None,False,0x7290f6,'eax'),
 (0x79f028,5,0x79ed73,94,0x79f03c,True,0x79f01b,'edx'),
]
from collections import Counter
print('=== P1 重复项值：目标块是否在入口即覆盖索引寄存器 ===')
for base,n,holder,bound,bt,two,dflt,idxreg in ROWS:
    vals=[u32(base+4*i) for i in range(n)]
    c=Counter(vals)
    dups={k:v for k,v in c.items() if v>1}
    if not dups: continue
    print(' table %s idx_reg=%s' % (hex(base), idxreg))
    for tgt,cnt in dups.items():
        ins=dis_at(tgt,4)
        print('   target %s x%d idx=%s' % (hex(tgt),cnt,[i for i,v in enumerate(vals) if v==tgt]))
        for i in ins: print('      %x %s' % (i.ip, F.format(i)))
        print('      is_default=%s' % (tgt==dflt))
print()
print('=== P2 直接形态：case 目标 == default 目标的项数 ===')
for base,n,holder,bound,bt,two,dflt,idxreg in ROWS:
    if two: continue
    vals=[u32(base+4*i) for i in range(n)]
    eq=[i for i,v in enumerate(vals) if v==dflt]
    print('  %s n=%d default=%s 命中项=%s' % (hex(base),n,hex(dflt),eq))
print()
print('=== P3 19 张 holder 的索引寄存器（由指令实测，不信 R105 的枚举数）===')
for base,n,holder,bound,bt,two,dflt,idxreg in ROWS:
    i=dis_at(holder,1)[0]
    mem=i.memory_index
    print('  %s holder=%s mem_index_enum=%s base=%s 声称=%s' % (hex(base),F.format(i),mem,hex(i.memory_displacement),idxreg))
print()
print('=== P4 两级表：byte 表值->case 的满射性反控素材（常量 0 化后能覆盖几个 case）===')
for base,n,holder,bound,bt,two,dflt,idxreg in ROWS:
    if not two: continue
    bs=raw[off(bt):off(bt)+bound+1]
    print('  %s 实测 distinct=%d / n=%d ; 常量0化 distinct=1 / n=%d' % (hex(base),len(set(bs)),n,n))
