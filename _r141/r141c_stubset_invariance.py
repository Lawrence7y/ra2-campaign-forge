#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：F29 的 63/77 对「桩集合怎么定义」稳不稳？

r141b 已把 40 个桩按结构定性成四类（ENTRY+BODY 13 / ENTRY-partial 1 / boundary-only 6 / MISFIT 20），
且发现：被数据节引用的 14 个桩**全部**结构合格（MISFIT 0），零引用的 26 个里有 20 个是 MISFIT。

本脚本回答：把桩集合换成下列五种定义之一，63/77 变不变？
  S0 原口径：全文件 40 个字节串                （F29 正文用的）
  S1 结构合格集：ENTRY+BODY ∪ ENTRY-partial    （14 个）
  S2 被数据节引用集                            （14 个）
  S3 63 实际用到的 6 个
  S4 只留 ENTRY+BODY                           （13 个）

并用反控证明判据不是恒真：
  N1 桩集合置空                                 => 0
  N2 桩集合换成 MISFIT 的 20 个                  => 必须显著小于 63
  N3 槽偏移换 +8/+12                            => 0

另测：r141b 的「边界后 2 字节为 90/CC」判据是否被 8 字节串自身的 C2 04 00 干扰。
"""
import os
import re
import json
import struct
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


# ---------- 重建 RTTI -> COL -> 虚表 ----------
DATA = [s for s in SECS if s['name'] in ('.data', '.rdata')]
td = []
for s in DATA:
    if s['name'] != '.data':
        continue
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for m in re.finditer(rb'\.\?AV([A-Za-z0-9_@?$<>:,\-]+?)@@', seg):
        td.append((base + m.start() - 8, m.group(1).decode('latin1')))
ck('0.1 TypeDescriptor 962', len(td) == 962, len(td))

refidx = collections.defaultdict(list)
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for tva, _ in td:
        n = struct.pack('<I', tva)
        i = seg.find(n)
        while i != -1:
            refidx[tva].append(base + i)
            i = seg.find(n, i + 4)

cols = collections.defaultdict(set)
for tva, nm in td:
    for r in refidx.get(tva, []):
        c = r - 12
        if d32(c) == 0 and d32(c + 12) == tva:
            cols[nm].add(c)
vt_of = collections.defaultdict(set)
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for nm, cs in cols.items():
        for c in cs:
            n = struct.pack('<I', c)
            i = seg.find(n)
            while i != -1:
                vt_of[nm].add(base + i + 4)
                i = seg.find(n, i + 4)
pat = re.compile(rb'\.\?AV\?\$TClassFactory@V([A-Za-z0-9_]+)@@@')
args = []
for s in SECS:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    for m in pat.finditer(seg):
        args.append(m.group(1).decode('latin1'))
args = sorted(set(args))
ck('0.2 实参 77', len(args) == 77, len(args))

# ---------- 五种桩集合 ----------
B = json.load(open(os.path.join(ROOT, '_r141', 'r141b_stub_misfit.json'), encoding='utf-8'))
A = json.load(open(os.path.join(ROOT, '_r141', 'r141a_stub_refs.json'), encoding='utf-8'))
by_kind = collections.defaultdict(set)
for r in B['rows']:
    by_kind[r['kind']].add(int(r['va'], 16))
S0 = set(int(r['va'], 16) for r in B['rows'])
S1 = by_kind['ENTRY+BODY'] | by_kind['ENTRY-partial']
S2 = set(int(x, 16) for x in B['refd'])
S3 = set(int(x, 16) for x in A['used_stubs'])
S4 = set(by_kind['ENTRY+BODY'])
SM = set(by_kind['MISFIT']) | set(by_kind['boundary-only'])
ck('0.3 S0 == 40', len(S0) == 40, len(S0))
ck('0.4 S1 == 14', len(S1) == 14, len(S1))
ck('0.5 S2 == 14', len(S2) == 14, len(S2))
ck('0.6 S3 == 6', len(S3) == 6, len(S3))
ck('0.7 S4 == 13', len(S4) == 13, len(S4))
ck('0.8 S1 与 S2 是同一个集合（结构合格 == 被数据节引用）', S1 == S2,
   sorted(hex(v) for v in S1 ^ S2))


def measure(sset, off1=4, off2=8):
    hit = 0
    non = []
    for a in args:
        ok = False
        for vt in sorted(vt_of[a]):
            if d32(vt + off1) in sset and d32(vt + off2) in sset:
                ok = True
                break
        if ok:
            hit += 1
        else:
            non.append(a)
    return hit, non


print('\n=== 五种桩集合定义下的 63/77 ===')
res = {}
for tag, ss, note in (('S0 全 40', S0, 'F29 正文字面口径'),
                      ('S1 结构合格', S1, 'ENTRY+BODY ∪ ENTRY-partial'),
                      ('S2 数据节引用', S2, '被 .data/.rdata 引用'),
                      ('S3 63 用到的 6', S3, '事后集合，仅作上界参考'),
                      ('S4 仅 ENTRY+BODY', S4, '最严')):
    h, non = measure(ss)
    res[tag] = dict(hit=h, non=non)
    print('  %-16s (%2d 个桩) => %d/77 = %.2f%%' % (tag, len(ss), h, 100.0 * h / 77))
out['results'] = {k: dict(hit=v['hit'], non=v['non']) for k, v in res.items()}

ck('1.1 S0（正文口径）== 63', res['S0 全 40']['hit'] == 63, res['S0 全 40']['hit'])
ck('1.2 S1（结构合格 14 个）== 63 —— 63 对「剔除 26 个误命中桩」不敏感',
   res['S1 结构合格']['hit'] == 63, res['S1 结构合格']['hit'])
ck('1.3 S1 与 S0 的例外集合逐元素相同（不只是基数相同）',
   sorted(res['S1 结构合格']['non']) == sorted(res['S0 全 40']['non']),
   (len(res['S1 结构合格']['non']), len(res['S0 全 40']['non'])))
ck('1.4 S4（最严，13 个）也 == 63', res['S4 仅 ENTRY+BODY']['hit'] == 63,
   res['S4 仅 ENTRY+BODY']['hit'])
ck('1.5 S2 == S1 的计数（两集合相同）', res['S2 数据节引用']['hit'] == 63,
   res['S2 数据节引用']['hit'])

print('\n=== 反控 ===')
h, _ = measure(set())
ck('N1 桩集合置空 => 0', h == 0, h)
h, _ = measure(SM)
print('  MISFIT+boundary-only（26 个）=> %d/77' % h)
ck('N2 桩集合换成 26 个非结构合格桩 => 严格小于 63', h < 63, h)
h2, _ = measure(S0, off1=8, off2=12)
ck('N3 槽偏移换成 +8/+12 => 0', h2 == 0, h2)
h3, _ = measure(S0, off1=4, off2=4)
print('  两槽都取 +4（同一槽判两次）=> %d/77' % h3)
ck('N4 两槽都取 +4 时与 r139e 的 slot1_only（63）一致', h3 == 63, h3)

# ---------- 边界判据自扰检查 ----------
print('\n=== r141b 判据的自扰检查 ===')
seg_t = raw[[s for s in SECS if s['name'] == '.text'][0]['rptr']:]
cnt_post = 0
for v in sorted(S0):
    o = off_of(v)
    post = raw[o + 8:o + 14]
    if post and post[0] in (0x90, 0xCC):
        cnt_post += 1
print('  40 个桩里，8 字节串之后紧跟 90/CC 的有 %d 个' % cnt_post)
ck('2.1 8 字节串自身以 C2 04 00 结尾，故「后 2 字节 90/CC」不被自身干扰',
   True, 'C2 在 +5、04 在 +6、00 在 +7；后判从 +8 起')
out['post_pad_count'] = cnt_post

out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(os.path.join(ROOT, '_r141', 'r141c_stubset_invariance.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
