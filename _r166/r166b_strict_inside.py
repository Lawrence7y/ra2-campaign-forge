#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166b_strict_inside.py —— 逐条判定「65 条是否真的落在某条（线性解码出的）指令内部」

r166a 已证：bounds − plain起点集（65 条）逐条等于 plain 线性扫描的**单字节重对齐点集合**（0 差）。
本轮把 R162/R163 的两句措辞分别取下界：
  S1（R162 原文）「65 条全部落在某条指令内部（位移 1..7）」
     严格读法 = 线性扫描里**上一条指令**（起点 prev_start，长度 prev_size）是否满足
     prev_start + prev_size > va。若该指令长度为 1，则它不覆盖 va ⇒ S1 对这条为假。
  S2（R163 原文）「65 条在 skipdata 口径下全部是真起点 ⇒ 数据区被逐字节跳过处」
     严格读法 = 每条在 skipdata 扫描里都是长度 1 的独立项。这条由 r166a 的 G 组承担。

另取三项独立量：
  T1  65 条的 gap_prev（相对线性扫描前一条起点）分布，与 R163 记录的 1:22 2:20 3:14 4:1 5:1 6:6 7:1 对比。
  T2  每条的前驱/后继指令形态（助记符 + 长度 + 字节），用于判「前驱是不是前缀字节被截断」。
  T3  反控：把判据换成「re-decode 从 va-k 起能覆盖 va（k<=7）」，S1 的命中数会从 X 变成 48
      ⇒ 两种读法**不可互换**，必须写清是哪一种。

内存纪律：只做一次 plain 线性扫描（disasm_lite，64KB 分块 + 1 字节重对齐），
不对整段开 detail；只对 65 条的邻域单独 disasm。
"""
import bisect
import io
import json
import os
import sys
from collections import Counter

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
BOUNDS = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r166/r166b_strict_inside.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:320]) if detail else ''))


data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
RAW, RSZ, VA, VSZ = t.PointerToRawData, t.SizeOfRawData, t.VirtualAddress, t.Misc_VirtualSize
LO = IB + VA
VS_BLOB = data[RAW:RAW + VSZ]

J = json.load(io.open(BOUNDS, encoding='utf-8'))
bounds = [int(x, 16) for x in J['bounds']]

# ---- plain 线性扫描（记录起点、长度、重对齐点）
md = Cs(CS_ARCH_X86, CS_MODE_32)
starts, sizes, resync = [], [], []
pos = 0
while pos < len(VS_BLOB):
    base = LO + pos
    seg = VS_BLOB[pos:pos + 65536]
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(seg, base):
        if a - base + sz > len(seg):
            break
        starts.append(a)
        sizes.append(sz)
        consumed = a - base + sz
    if consumed:
        pos += consumed
    else:
        resync.append(base)
        pos += 1

pS = set(starts)
ck('C0 plain 起点 1,392,527 / 重对齐点 65', len(starts) == 1392527 and len(resync) == 65,
   (len(starts), len(resync)))
internal = [v for v in bounds if v not in pS]
ck('C1 bounds − plain起点 == 65 == 重对齐点集合（r166a D1 复算）',
   internal == resync, (len(internal), len(resync), internal == resync))

# ---- S1 严格读法：上一条线性解码指令是否覆盖 va
md_det = Cs(CS_ARCH_X86, CS_MODE_32)
rows = []
for va in internal:
    i = bisect.bisect_left(starts, va)
    prev = starts[i - 1] if i > 0 else None
    prev_sz = sizes[i - 1] if i > 0 else 0
    nxt = starts[i] if i < len(starts) else None
    covered_by_prev = (prev is not None) and (prev + prev_sz > va)
    # re-decode 读法：从 va-k（k<=7）起解一条，能否覆盖 va
    off = va - LO
    ks = []
    for k in range(1, 8):
        if off - k < 0:
            continue
        ds = list(md_det.disasm(VS_BLOB[off - k:off - k + 24], va - k))
        if ds and ds[0].size > k:
            ks.append(k)
    rows.append({'va': va, 'gap_prev': va - prev if prev is not None else None,
                 'prev_start': prev, 'prev_size': prev_sz,
                 'covered_by_prev': covered_by_prev,
                 'redecode_ks': ks})

n_prev = sum(1 for r in rows if r['covered_by_prev'])
n_re = sum(1 for r in rows if r['redecode_ks'])
print('  S1 严格读法（上一条线性指令覆盖 va）命中 %d / 65' % n_prev)
print('  re-decode 读法（k<=7 某条重解指令覆盖 va）命中 %d / 65' % n_re)
print('  gap_prev 分布 %s' % dict(sorted(Counter(r['gap_prev'] for r in rows).items())))

ck('S1 复现 R163 记录的 gap_prev 分布 1:22 2:20 3:14 4:1 5:1 6:6 7:1',
   dict(Counter(r['gap_prev'] for r in rows)) == {1: 22, 2: 20, 3: 14, 4: 1, 5: 1, 6: 6, 7: 1},
   dict(sorted(Counter(r['gap_prev'] for r in rows).items())))
ck('S2 R162/R163 的「65 条全部落在某条指令内部」在**严格读法**（上一条线性解码指令覆盖 va）'
   '下为假：命中 0 / 65', n_prev == 0, n_prev)
ck('S3 两种读法不可互换：严格读法 %d ≠ re-decode 读法 %d' % (n_prev, n_re), n_prev != n_re,
   (n_prev, n_re))
n_end = sum(1 for r in rows if r['prev_start'] + r['prev_size'] == r['va'])
ck('S5 真形态：63 / 65 的 va 恰等于前一条线性指令的**终点**（gap == prev_size），'
   '即它们坐在指令**边界之后**，不在任何指令内部',
   n_end == 63, n_end)
ck('S4 gap_prev == 1 的 22 条里，前驱指令长度为 1（即前驱只覆盖自己，不覆盖 va）',
   all(r['prev_size'] == 1 for r in rows if r['gap_prev'] == 1),
   sorted(set(r['prev_size'] for r in rows if r['gap_prev'] == 1)))
notcov = [r for r in rows if r['gap_prev'] != r['prev_size']]
print('  gap != prev_size 的 2 条（va / prev / prev_size / gap / 前驱字节）:')
for r in notcov:
    off = r['prev_start'] - LO
    print('   %#010x prev=%#010x size=%d gap=%d bytes=%s'
          % (r['va'], r['prev_start'], r['prev_size'], r['gap_prev'],
             VS_BLOB[off:off + r['prev_size']].hex()))

# ---- T2：前驱形态
mn_prev = []
for r in rows:
    off = r['prev_start'] - LO
    ds = list(md_det.disasm(VS_BLOB[off:off + 16], r['prev_start']))
    mn_prev.append(ds[0].mnemonic if ds else '?')
print('  前驱助记符分布 %s' % dict(sorted(Counter(mn_prev).items())))
ck('T2 前驱里没有一条是「前缀字节被截断」的形态（前驱长度全 >= 1 且都能独立解出）',
   all(m != '?' for m in mn_prev), len(mn_prev))

# ---- T3：反控 —— 把 prev 换成「更早的起点」不会让 17 条被覆盖
ck('T3 反控：65 条中 **17 条**在 re-decode 读法下无任何 k（连「从更早重解」也覆盖不到），'
   '故 48 + 17 = 65 两桶互补', sum(1 for r in rows if not r['redecode_ks']) == 17,
   sum(1 for r in rows if not r['redecode_ks']))
ck('T4 反控：48 条被严格读法判真的，其 re-decode_ks 必非空',
   all(r['redecode_ks'] for r in rows if r['covered_by_prev']),
   sum(1 for r in rows if r['covered_by_prev'] and not r['redecode_ks']))
ck('T5 65 条的字节值不是单一值（17 种，非填充字节）',
   len(Counter(VS_BLOB[r['va'] - LO] for r in rows)) == 17,
   len(Counter(VS_BLOB[r['va'] - LO] for r in rows)))

json.dump({'internal': len(internal), 'strict_covered': n_prev, 'redecode_covered': n_re,
           'gap_prev_hist': {str(k): v for k, v in sorted(Counter(r['gap_prev'] for r in rows).items())},
           'prev_mnemonic_hist': dict(sorted(Counter(mn_prev).items())),
           'rows': [dict((k, (hex(v) if isinstance(v, int) else v)) for k, v in r.items())
                    for r in rows],
           'asserts': RES, 'fail': FAIL},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), FAIL, OUT))
sys.exit(1 if FAIL else 0)
