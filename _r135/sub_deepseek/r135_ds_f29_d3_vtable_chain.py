# -*- coding: utf-8 -*-
"""R135-DS · F29 旁证 2（只读）: vtable[-4]->COL->TD->name 链，确认 0x6C2AC0 / 0x6C51C0 归属；
以及 0x7E11C8 指向的 0x0040F990 处是什么。"""
import struct, io
D = io.open('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe','rb').read()
e = struct.unpack_from('<I', D, 0x3C)[0]; nsec = struct.unpack_from('<H', D, e+6)[0]
opt = e+24; IMG = 0x400000; soh = struct.unpack_from('<H', D, e+20)[0]
S = []
for i in range(nsec):
    o = opt+soh+i*40; nm = D[o:o+8].rstrip(b'\0').decode()
    vs, va, rs, ro = struct.unpack_from('<IIII', D, o+8); S.append((nm, va, vs, ro, rs))
def off(rva):
    for nm, va, vs, ro, rs in S:
        if va <= rva < va+max(vs, rs): return ro+(rva-va)
def dw(va): return struct.unpack_from('<I', D, off(va-IMG))[0]
def cstr(rva, n=128):
    o = off(rva); return D[o:o+n].split(b'\0')[0].decode('latin-1')

print('--- vtable 链（vtable[-4] -> COL -> COL+0xC -> TD -> TD+8 名字）---')
for vt in (0x7F3B28, 0x7F3D98):
    col = dw(vt-4); td = dw(col+0xC) if col else 0
    nmrva = td+8
    print('vtable=0x%08X  [-4](COL)=0x%08X  COL+0xC(TD)=0x%08X  TD+8 名串 RVA=0x%06X 名=%r'
          % (vt, col, td, nmrva-IMG if td else 0, cstr(nmrva-IMG) if td else ''))
    print('   vtable[0..4] = ' + ' '.join('0x%08X' % dw(vt+4*i) for i in range(4)))

print('\n--- 0x7E11C8 IAT 槽磁盘值 0x0040F990 处内容 ---')
o = off(0x0040F990-IMG)
print('off=0x%06X bytes: %s' % (o, ' '.join('%02X'%b for b in D[o:o+32])))
# 该处若为 FF 25 xx xx xx xx 则是跳板
print('首字节 = 0x%02X (0xE9=jmp rel32, 0xFF=jmp/call indirect, 0x8B=mov)' % D[o])
if D[o] == 0xE9:
    rel = struct.unpack_from('<i', D, o+1)[0]; print('  jmp rel32 -> 0x%08X' % (0x0040F990+5+rel))
if D[o] == 0xFF and D[o+1] == 0x25:
    tgt = struct.unpack_from('<I', D, o+2)[0]; print('  jmp [0x%08X] -> ' % tgt)
# 该 .text 目标处的 IBN 名是什么？反查：
# 在 .detour IBN 区，若 339 个 IAT 槽都预填 .text 地址，则 InterlockedIncrement 的实际体在 0x40F990 或其跳板
print('\n--- 全 IAT 槽预填值是否都指向 .text 且唯一 ---')
imp = struct.unpack_from('<I', D, opt+96+8)[0]
descs = []
for i in range(64):
    oo = off(imp+i*20); t = struct.unpack_from('<5I', D, oo)
    if t == (0,)*5: break
    descs.append((cstr(t[3]), t[0], t[4]))
vals = []
for nm, oft, ft in descs:
    ilt = oft or ft; j = 0
    while True:
        iv = struct.unpack_from('<I', D, off(ilt+j*4))[0]
        if iv == 0: break
        if not (iv & 0x80000000):
            vals.append(struct.unpack_from('<I', D, off(ft+j*4))[0])
        else:
            vals.append(None)
        j += 1
real = [v for v in vals if v]
print('按名条目 %d 条，预填 .text 地址 %d 条，不同地址 = %d' % (len(vals)-33, len(real), len(set(real))))
import collections
c = collections.Counter(real)
print('出现 >1 次的预填地址数 = %d ; 最多重复 %d' % (sum(1 for k,v in c.items() if v>1), max(c.values())))
print('0x0040F990 在预填值中出现次数 = %d' % c.get(0x0040F990, 0))
