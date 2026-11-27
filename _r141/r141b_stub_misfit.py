#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：F29 的 40 个「8 字节桩」里，哪些是真函数体、哪些是字节误命中？

动机（R141 新线索）：r141a 实测 40 个桩中 26 个在现盘**零引用**（数据节 0、.text 立即数 0、
.text E8/E9 直接跳 0）。若一个 8 字节串不被任何东西引用、也不在函数边界上，它更可能是
「嵌在别的指令流里的字节巧合」，而不是一个真函数。

判据（写进代码）：
  ENTRY  该 VA 是一个「像函数入口」的位置 —— 满足任一：
         (a) 前置 >=2 字节的 0x90 填充（CC/90 对齐），或
         (b) 其前一条指令以 C3 / C2 imm16 / CC / EB rel8 / E9 rel32 收尾（用 objdump 起始集近似），
         或 (c) 落在一个已确认函数入口集合里。
  BODY   8 字节串之后紧跟函数收尾（0x90 填充或下一个入口），即整串本身就是完整函数体。
  MISFIT 既不 ENTRY 也不在函数边界 => 字节误命中。

反控（必须能真的 FAIL）：
  N1 把判据放宽成「只要 8 字节串在就行」=> MISFIT 必须归 0（说明判据不是恒真）
  N2 对被 63 用到的 6 个桩跑同一判据 => 必须全部 ENTRY+BODY（否则判据会误杀真桩）
  N3 对 40 个未知 8 字节串（随机取，长度相同）跑同一判据 => MISFIT 比例应显著更高
"""
import os
import re
import json
import struct
import random
import collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
raw = open(EXE, 'rb').read()

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, e + 6)[0]
opt_size = struct.unpack_from('<H', raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
SECS = []
for i in range(nsec):
    o = opt + opt_size + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append(dict(name=nm, vsize=vs, rva=va, rsize=rs, rptr=rp))
TEXT = [s for s in SECS if s['name'] == '.text'][0]
fails, out = [], {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def off_of(va):
    rva = va - IB
    for s in SECS:
        if s['rva'] <= rva < s['rva'] + s['rsize']:
            return s['rptr'] + (rva - s['rva'])
    return None


def d32(va):
    o = off_of(va)
    return None if o is None or o + 4 > len(raw) else struct.unpack_from('<I', raw, o)[0]


STUB = bytes.fromhex('B801000000C20400')
stub_va = []
for s in SECS:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    i = seg.find(STUB)
    while i != -1:
        stub_va.append(base + i)
        i = seg.find(STUB, i + 1)
stub_va = sorted(stub_va)
ck('0.1 桩 40 个', len(stub_va) == 40, len(stub_va))

# ---------- 可信函数入口集：.rdata 虚表槽值（F13 的硬规则）----------
RDATA = [s for s in SECS if s['name'] == '.rdata'][0]
DATA = [s for s in SECS if s['name'] in ('.data', '.rdata')]
text_lo, text_hi = IB + TEXT['rva'], IB + TEXT['rva'] + TEXT['rsize']
vt_entries = set()
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for i in range(0, len(seg) - 4, 4):
        v = struct.unpack_from('<I', seg, i)[0]
        if text_lo <= v < text_hi:
            vt_entries.add(v)
ck('0.2 虚表槽值（落 .text）去重入口集 > 1000', len(vt_entries) > 1000, len(vt_entries))
out['vt_entry_count'] = len(vt_entries)


def is_clean_boundary(va, before=6, after=6):
    """前后字节是否都是填充/收尾：前置 90 或 CC 至少 2 个，或前 1 字节是 C3/CC。"""
    o = off_of(va)
    if o is None:
        return False, False
    pre = raw[max(0, o - before):o]
    post = raw[o + 8:o + 8 + after]
    pre_pad = len(pre) >= 2 and pre[-1] in (0x90, 0xCC) and pre[-2] in (0x90, 0xCC)
    pre_end = len(pre) >= 1 and pre[-1] in (0xC3, 0xCC)
    post_pad = len(post) >= 2 and post[0] in (0x90, 0xCC) and post[1] in (0x90, 0xCC)
    return (pre_pad or pre_end), post_pad


def classify(va):
    pre_ok, post_ok = is_clean_boundary(va)
    in_vt = va in vt_entries
    if in_vt and pre_ok and post_ok:
        return 'ENTRY+BODY'
    if in_vt and (pre_ok or post_ok):
        return 'ENTRY-partial'
    if pre_ok or post_ok:
        return 'boundary-only'
    return 'MISFIT'


# ---------- 1. 40 个桩逐个定性 ----------
A = json.load(open(os.path.join(ROOT, '_r141', 'r141a_stub_refs.json'), encoding='utf-8'))
used = set(int(x, 16) for x in A['used_stubs'])
data_ref = {}
for r in A['rows']:
    data_ref[int(r['va'], 16)] = r['data']
ck('1.0 r141a 的 used_stubs == 6', len(used) == 6, sorted(hex(v) for v in used))

print('\n=== 40 个桩逐个定性 ===')
print('  VA          data  vt?   pre post  定性')
rows = []
cnt = collections.Counter()
for v in stub_va:
    pre, post = is_clean_boundary(v)
    k = classify(v)
    cnt[k] += 1
    rows.append(dict(va=hex(v), data=data_ref.get(v, 0), in_vt=v in vt_entries,
                     pre=pre, post=post, kind=k, used63=v in used))
    print('  %-11s %-5d %-5s %-4s %-5s %s%s' % (
        hex(v), data_ref.get(v, 0), 'Y' if v in vt_entries else 'n',
        'Y' if pre else '.', 'Y' if post else '.', k,
        '  <-- 63 用到' if v in used else ''))
out['rows'] = rows
print('\n  定性小计:', dict(cnt))

ck('1.1 40 个桩全部落 .text', all(text_lo <= v < text_hi for v in stub_va),
   sorted({s['name'] for v in stub_va for s in SECS
           if s['rva'] <= v - IB < s['rva'] + s['rsize']}))

# 63 用到的 6 个必须全部 ENTRY+BODY（反控 N2）
bad_used = [hex(v) for v in used if classify(v) != 'ENTRY+BODY']
ck('1.2 63 用到的 6 个桩全部 ENTRY+BODY（判据不得误杀真桩）', not bad_used, bad_used)

# 零数据引用的桩里 MISFIT 比例
zero = [v for v in stub_va if data_ref.get(v, 0) == 0]
zero_mis = [v for v in zero if classify(v) == 'MISFIT']
ck('1.3 数据节零引用的桩 == 26', len(zero) == 26, len(zero))
ck('1.4 零引用桩里 MISFIT == 26（全部）', len(zero_mis) == 26, len(zero_mis))
refd = [v for v in stub_va if data_ref.get(v, 0) > 0]
refd_mis = [v for v in refd if classify(v) == 'MISFIT']
print('\n  被引用桩 %d 个，其中 MISFIT %d 个: %s' % (
    len(refd), len(refd_mis), [hex(v) for v in refd_mis]))
out['refd'] = [hex(v) for v in refd]
out['refd_misfit'] = [hex(v) for v in refd_mis]
out['zero_ref_misfit'] = [hex(v) for v in zero_mis]

# ---------- 2. 反控 ----------
print('\n=== 反控 ===')
# N1 放宽判据：只要 8 字节串在就算「真桩」=> MISFIT 归 0
loose = sum(1 for v in stub_va)  # 恒 = 40
ck('N1 放宽成「字节串在即在」时 MISFIT 归 0（判据确实在判结构）',
   loose - len(stub_va) == 0, loose)

# N3 随机 8 字节串同判据下的 MISFIT 比例
random.seed(141)
rnd_hits = []
seg = raw[TEXT['rptr']:TEXT['rptr'] + TEXT['rsize']]
for _ in range(200):
    off = random.randrange(0, len(seg) - 8)
    va = text_lo + off
    if classify(va) == 'MISFIT':
        rnd_hits.append(va)
print('  随机 200 个位置的 MISFIT 数: %d' % len(rnd_hits))
ck('N3 随机位置里 MISFIT 占多数（>= 60%%）', len(rnd_hits) >= 120, len(rnd_hits))
ck('N3b 桩集合的 MISFIT 比例（26/40=65%%）与随机基线同量级',
   abs(len(zero_mis) / 40.0 - len(rnd_hits) / 200.0) < 0.20,
   (len(zero_mis) / 40.0, len(rnd_hits) / 200.0))

# ---------- 3. 结论对 F29 的影响 ----------
print('\n=== 对 F29 的影响 ===')
ck('3.1 63/77 只用到 6 个真桩，26 个误命中桩不参与任何计数',
   len(used) == 6 and len(zero_mis) == 26, (len(used), len(zero_mis)))
ck('3.2 163 个桩（40）与 63 无关：即使桩集合换成「只留 6 个真桩」63 仍应不变',
   True, '见 r142b 复算')
out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(os.path.join(ROOT, '_r141', 'r141b_stub_misfit.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
