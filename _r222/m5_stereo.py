# -*- coding: utf-8 -*-
"""R222 m5: stereo 双遍结构判定。

待判命题：
  P1 0x7c7b4c 起的区域是「第二遍」入口派发（与 0x7c7788 同构），其 4 项对齐表 = 0x7c7f10。
  P2 两遍的 nibble 取法互补：一遍走低半字节出口（表 A 0x87bc90），另一遍走高半字节出口（表 B 0x87bd90）。
  P3 两遍的 edi 写偏移互补（一遍 0,4,8,...,1c；另一遍 2,6,a,...,1e），合起来填满 0x20 字节 = 8 帧。
  P4 0x7c7bc0 无外部入边，只从 0x7c7b4c 派发进入。
反控：
  R1 若把 P3 判为「两遍偏移相同」，则在 0x7c7bc0..0x7c7d4a 内应能找到与遍一相同的 store 偏移序列 —— 报告实测偏移表。
  R2 两遍 nibble 出口表若相同，则高半字节表引用计数应为 0 —— 报告实测。
"""
import sys, re, struct
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True


def dis(lo, hi):
    o = P.r2o(lo)
    buf = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(buf, lo)]


print('=== 0x7c7b3c..0x7c7bc0（stereo 遍一收尾 + 遍二派发候选区） ===')
for a, b, mn, op in dis(0x7c7b3c, 0x7c7bc0):
    print('%08x  %-20s %s %s' % (a, b, mn, op))

print()
print('=== 遍二入口头 0x7c7bc0..0x7c7c10 ===')
for a, b, mn, op in dis(0x7c7bc0, 0x7c7c10):
    print('%08x  %-20s %s %s' % (a, b, mn, op))

print()
print('=== 遍二尾部 0x7c7d2a..0x7c7d60 ===')
for a, b, mn, op in dis(0x7c7d2a, 0x7c7d60):
    print('%08x  %-20s %s %s' % (a, b, mn, op))

print()
print('=== 遍一尾部 0x7c7955..0x7c797a（已知）与 0x7c7989..0x7c79a0 ===')
for a, b, mn, op in dis(0x7c7989, 0x7c79a0):
    print('%08x  %-20s %s %s' % (a, b, mn, op))


def stores(lo, hi):
    out = []
    for a, b, mn, op in dis(lo, hi):
        m = re.match(r'word ptr \[edi(?: \+ (0x[0-9a-f]+))?\], ax$', op)
        if mn == 'mov' and m:
            off = int(m.group(1), 16) if m.group(1) else 0
            out.append((hex(a), off))
    return out


print()
print('=== P3 store 偏移实测 ===')
s1 = stores(0x7c77f0, 0x7c797a)
s2 = stores(0x7c7bc0, 0x7c7d4a)
print('遍一 0x7c77f0 偏移:', [o for _, o in s1])
print('遍二 0x7c7bc0 偏移:', [o for _, o in s2])
print('遍一 == 遍二 ?', [o for _, o in s1] == [o for _, o in s2])
u = sorted(set([o for _, o in s1]) | set([o for _, o in s2]))
v = sorted(set([o for _, o in s1]) & set([o for _, o in s2]))
print('并集:', u)
print('交集:', v)
print('并集是否恰为 0..0x1e 偶数步 16 项:', u == list(range(0, 0x20, 2)))


def nib_tables(lo, hi):
    out = []
    for a, b, mn, op in dis(lo, hi):
        m = re.search(r'\[ebx \+ 0x(87bc90|87bd90)\]', op)
        if m:
            out.append((hex(a), m.group(1)))
    return out


print()
print('=== P2 nibble 出口表实测 ===')
n1 = nib_tables(0x7c77f0, 0x7c797a)
n2 = nib_tables(0x7c7bc0, 0x7c7d4a)
print('遍一出口表序列:', n1)
print('遍二出口表序列:', n2)
print('遍一 低半字节/nibble 移位指令:', [(hex(a), op) for a, b, mn, op in dis(0x7c77f0, 0x7c797a)
                                         if mn in ('shr', 'shl', 'mov') and ('ecx' in op or 'bl' in op)][:24])
print('遍二 低半字节/nibble 移位指令:', [(hex(a), op) for a, b, mn, op in dis(0x7c7bc0, 0x7c7d4a)
                                         if mn in ('shr', 'shl', 'mov') and ('ecx' in op or 'bl' in op)][:24])

print()
print('=== P1/P4 入边核对（0x7c7350..0x7c7f30 内所有直接分支） ===')
seq = dis(0x7c7350, 0x7c7f30)
edges = [(a, int(op, 16), mn) for a, b, mn, op in seq if mn.startswith('j') and op.startswith('0x')]
for tgt in (0x7c7788, 0x7c7b4c, 0x7c7bc0, 0x7c7f10, 0x7c7ef0, 0x7c7b1c):
    print('%08x 入边: %s' % (tgt, [(hex(f), k) for f, t, k in edges if t == tgt] or 'NONE（间接或段外）'))
for a, b, mn, op in seq:
    if mn == 'jmp' and '[' in op:
        print('  间接跳转 %08x: %s' % (a, op))
