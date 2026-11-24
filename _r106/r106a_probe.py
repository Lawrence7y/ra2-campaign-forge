#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106a_switchmap.py —— 探测阶段（先实测再定断言）

目标（R105 待办②③）：
  ② 10 张两级形态表的「输入 -> case」分组未逐表列出（BOUND+1 个输入映射到 n 个 case）
  ③ 直接形态表 0x728e08 有 4 项同值 0x728de0，这 4 个 case 是否真等价未证

本脚本只打印实测值，不写断言；数字定型后由 r106b 带断言正式出。
"""
import struct, sys, os

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, '_r104/vendor')
import iced_x86

F = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)
raw = open('ra2bench/gamemd.exe', 'rb').read()

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))

def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None

def sec_of(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return nm
    return None

def u32(va):
    return struct.unpack_from('<I', raw, off(va))[0]

def dis_at(va, n=1):
    o = off(va)
    dec = iced_x86.Decoder(32, raw[o:o + 15 * n + 32], ip=va)
    out = []
    for _ in range(n):
        if not dec.can_decode:
            break
        i = dec.decode()
        out.append(i)
    return out

def dump(va, n=1):
    return [(hex(i.ip), F.format(i), i.len) for i in dis_at(va, n)]

ROWS = [
    # table, n, holder, bound, byte_table, two_level
    (0x46f5a0, 4, 0x46e4be, 47, 0x46f5b0, True),
    (0x48db10, 13, 0x48d583, 37, 0x48db44, True),
    (0x48dd10, 5, 0x48dce0, 39, 0x48dd24, True),
    (0x4c8114, 46, 0x4c6cd7, 45, None, False),
    (0x5001e4, 5, 0x4ffde9, 4, None, False),
    (0x58bda4, 5, 0x58bd85, 4, None, False),
    (0x69b15c, 4, 0x69af3e, 3, None, False),
    (0x6a92c4, 3, 0x6a8e1e, 14, 0x6a92d0, True),
    (0x6adbdc, 3, 0x6acf2a, 22, 0x6adbe8, True),
    (0x6b0238, 7, 0x6afd73, 6, None, False),
    (0x6dfdec, 145, 0x6dd8e7, 144, None, False),
    (0x708d54, 5, 0x708c4e, 4, None, False),
    (0x71f2c0, 14, 0x71eea2, 45, 0x71f2f8, True),
    (0x71f328, 10, 0x71f092, 55, 0x71f350, True),
    (0x71f778, 2, 0x71f6d0, 55, 0x71f780, True),
    (0x71f9e0, 2, 0x71f9d3, 58, 0x71f9e8, True),
    (0x728e08, 7, 0x728c17, 6, None, False),
    (0x7291ac, 7, 0x728e6c, 6, None, False),
    (0x79f028, 5, 0x79ed73, 94, 0x79f03c, True),
]

def norm_before(holder):
    """从 holder 往前 96 B 线性解码，取最后一对 cmp/jcc 与其间指令"""
    lo = holder - 96
    dec = iced_x86.Decoder(32, raw[off(lo):off(lo) + 96], ip=lo)
    ins = []
    while dec.can_decode and dec.ip < holder:
        ins.append(dec.decode())
    tail = ins[-6:]
    return [(hex(i.ip), F.format(i)) for i in tail]

print('=== S1 19 张表：项值重复普查 ===')
tot_entries = 0
tot_dupes = 0
for base, n, holder, bound, bt, two in ROWS:
    vals = [u32(base + 4 * i) for i in range(n)]
    uniq = len(set(vals))
    dup = n - uniq
    tot_entries += n
    tot_dupes += dup
    flags = ''
    if dup:
        from collections import Counter
        c = Counter(vals)
        flags = ' DUP:' + str([(hex(k), v) for k, v in c.items() if v > 1])
    print('  %s n=%3d uniq=%3d dup=%3d two=%-5s%s'
          % (hex(base), n, uniq, dup, two, flags))
print('  合计 entries=%d dup=%d' % (tot_entries, tot_dupes))

print('\n=== S2 10 张两级表：输入 -> case 分组 ===')
for base, n, holder, bound, bt, two in ROWS:
    if not two:
        continue
    nbytes = bound + 1
    bs = raw[off(bt):off(bt) + nbytes]
    print('  %s n=%d bound=%d nbytes=%d maxbyte=%d' % (hex(base), n, bound, nbytes, max(bs)))
    print('    holder 前置: %s' % (norm_before(holder),))
    from collections import Counter, defaultdict
    g = defaultdict(list)
    for v, b in enumerate(bs):
        g[b].append(v)
    sizes = sorted(((k, len(v)) for k, v in g.items()))
    print('    分组 (case_idx -> 输入个数): %s' % sizes)
    print('    未用到的 case idx: %s' % [i for i in range(n) if i not in g])
    multi = {k: v for k, v in g.items() if len(v) > 1}
    print('    多输入共用 case: %s' % {k: (len(v), v[:6]) for k, v in multi.items()})
    print('    sum(sizeofgroups)=%d 应等于 %d' % (sum(len(v) for v in g.values()), nbytes))

print('\n=== S3 表 0x728e08 的 4 个同值项 ===')
base = 0x728e08
vals = [u32(base + 4 * i) for i in range(7)]
print('  entries:', [hex(v) for v in vals])
from collections import Counter
c = Counter(vals)
for va, cnt in c.items():
    idx = [i for i, v in enumerate(vals) if v == va]
    print('  target %s 被 %d 项引用, indices=%s' % (hex(va), cnt, idx))
for va in (0x728de0, 0x728dd9, 0x728dd0, 0x728c1e):
    print('  --- %s :' % hex(va))
    for t in dump(va, 6):
        print('       %s %s' % (t[0], t[1]))

print('\n  0x728e08 前置:', norm_before(0x728c17))

print('\n=== S4 反控素材：全库 19 表以外是否有同值项 ===')
print('  0x728dd9 与 0x728dd0 相差 %d B' % (0x728dd9 - 0x728dd0))
print('  0x728de0 与 0x728dd9 相差 %d B' % (0x728de0 - 0x728dd9))
for va in (0x728dd0, 0x728dd9, 0x728de0, 0x728c1e):
    i = dis_at(va, 1)[0]
    print('  %s -> %s len=%d cc=%s' % (hex(va), F.format(i), i.len, i.code))
