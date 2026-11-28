# -*- coding: utf-8 -*-
"""R222 m9：stereo 两遍的 word 下标互补（声道交错）严格证明 + 反控。

命题：pass1 的 8 个 store（字节偏移 0,4,..,0x1c）对应 word 下标 0,2,..,14；
      pass2 同样的 8 个字节偏移，但入口多 add edi,2，故对应 word 下标 1,3,..,15。
      并集 = 0..15（16 word = 32 B），交集 = 空。
反控：
  R1 若 pass2 入口没有 add edi,2，则两遍都占 0,2,..,14，并集只有 8 个 word（覆盖半帧）。
  R2 mono 入口无 edi 偏置（对照）。
"""
import sys, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def dis(lo, hi):
    o = P.r2o(lo)
    b = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(b, lo)]


def offs(lo, hi):
    out = []
    for a, b, mn, op in dis(lo, hi):
        m = re.match(r'word ptr \[edi(?: \+ ([0-9a-fx]+))?\], ax$', op)
        if mn == 'mov' and m:
            out.append(int(m.group(1), 0) if m.group(1) else 0)
    return out


def entry_items(lo, hi):
    return [(a, mn, op) for a, b, mn, op in dis(lo, hi)]


o1 = offs(0x7c77f0, 0x7c7982)
o2 = offs(0x7c7bc0, 0x7c7d4a)
ck('S1 pass1 8 个 store 字节偏移 0,4,..,0x1c', o1 == list(range(0, 0x20, 4)), o1)
ck('S2 pass2 8 个 store 字节偏移 0,4,..,0x1c', o2 == list(range(0, 0x20, 4)), o2)

e1 = entry_items(0x7c7788, 0x7c7798)
e2 = entry_items(0x7c7b4c, 0x7c7b62)
e0 = entry_items(0x7c73c3, 0x7c73d3)
add1 = [(a, mn, op) for a, mn, op in e1 if mn == 'add' and op.startswith('edi,')]
add2 = [(a, mn, op) for a, mn, op in e2 if mn == 'add' and op.startswith('edi,')]
add0 = [(a, mn, op) for a, mn, op in e0 if mn == 'add' and op.startswith('edi,')]
ck('S3 pass1 入口无 edi 偏置', add1 == [], add1)
ck('S4 pass2 入口有 add edi,2（0x7c7b54）', add2 == [(0x7c7b54, 'add', 'edi, 2')], add2)
ck('S5 mono 入口无 edi 偏置（对照）', add0 == [], add0)

w1 = sorted(x // 2 for x in o1)
w2 = sorted(x // 2 + 1 for x in o2)
ck('S6 pass1 word 下标 0,2,..,14', w1 == list(range(0, 16, 2)), w1)
ck('S7 pass2 word 下标 1,3,..,15', w2 == list(range(1, 16, 2)), w2)
ck('S8 并集 = 0..15（16 word = 32 B = 16 个 16 位立体声样本）',
   sorted(set(w1) | set(w2)) == list(range(16)), sorted(set(w1) | set(w2)))
ck('S9 交集为空（两遍不写同一 word）', sorted(set(w1) & set(w2)) == [], sorted(set(w1) & set(w2)))
ck('R1 反控：去掉 +2 B 偏置后并集只剩 8 word、覆盖半帧',
   sorted(set(w1) | set(x // 2 for x in o2)) == list(range(0, 16, 2)),
   sorted(set(w1) | set(x // 2 for x in o2)))
ck('R2 mono 体偏移 0,2,..,0xe 与 stereo 不同（8 word = 16 B 单声道）',
   offs(0x7c7428, 0x7c75b2) == list(range(0, 0x10, 2)), offs(0x7c7428, 0x7c75b2))

# pass2 的源指针挪动
src = [(a, mn, op) for a, mn, op in e2 if ('edx' in op or 'esi' in op)]
ck('S10 pass2 入口 mov edx,[ebp+0x18]; shr edx,3; add esi,edx（源指针错开一帧/8）',
   any(mn == 'mov' and op == 'edx, dword ptr [ebp + 0x18]' for a, mn, op in src) and
   any(mn == 'shr' and op == 'edx, 3' for a, mn, op in src) and
   any(mn == 'add' and op == 'esi, edx' for a, mn, op in src), src)

print()
print('FAIL 数 =', len(fails), fails)
if fails:
    raise SystemExit(1)
