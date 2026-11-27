#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166d_write_v546.py —— FACT_INDEX V545 -> V546（F24 limitations 追加 R166 段）

本轮改的是**一处数字解释的措辞**，不改任何计数：
  R162/R163 三处轮次记录里写的「在 bounds 但非起始 65 条全部落在某条指令内部（位移 1..7）」
  在严格读法下**为假**（命中 0/65），已由 _r166/r166a（25 断言）与 r166b（11 断言）实测：
    * 65 条 == plain 线性扫描的单字节重对齐点集合（对称差 0）；
    * 63 条 va 恰等于前一条线性解码指令的**终点**（gap == prev_size）⇒ 坐在边界之后；
    * 48 条在某 k<=7「重解一条覆盖 va」，17 条连这个也覆盖不到；
    * 「位移 1..7」的真身 = va 相对前一条起点的距离分布（1:22 2:20 3:14 4:1 5:1 6:6 7:1）。
  故在 F24 limitations 末尾追加一段，把这些分量写清，并把「不得把距离当内部」写成纪律。

只改 F24 第 5 列（追加），其余 53 行 × 5 列逐字节不变；前四列不动。
写入纪律：wx 独占备份 -> 断言旧 sha256/CR -> 一次性写 -> 回读 sha/行数/列数/逐行差分。
"""
import hashlib
import io
import json
import os
import shutil
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V545 = os.path.join(T, 'R17_R117_FACTINDEX_V545/FACT_INDEX.tsv')
V546D = os.path.join(T, 'R17_R118_FACTINDEX_V546')
V546 = os.path.join(V546D, 'FACT_INDEX.tsv')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r166/r166d_write_v546.json')

V545_SHA = '5707594f5da566ce4faf5c92dc6c910d9fa4ea96409c3d79be84148e65bd18e4'
V545_BYTES = 104017

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


APPEND = (
    '**【R166 补·那 65 条的形态被重新定性，R162/R163 的措辞为假】** '
    '上文 R162 段与本条轮次记录里写的「在 `bounds` 但非起始 **65** 条**全部落在某条指令内部**（位移 1..7）」，'
    '在**严格读法**（上一条线性解码指令的区间覆盖该 VA）下命中 **0 / 65**，该措辞**为假**；'
    '本轮给出四条可失败分量（`_r166/r166a_internal_targets.py` 25 断言 0 FAIL、`_r166/r166b_strict_inside.py` 11 断言 0 FAIL）：'
    '① 那 65 条**逐位等于** plain（capstone 无 skipdata、VirtualSize blob、64KB 分块 + 1 字节重对齐）线性扫描的'
    '**单字节重对齐点集合**，对称差 **0**（`only_in_bounds=0 only_in_resync=0`）⇒ 它们是「线性解码在此处解不出指令、'
    '只能前进 1 字节」的**洞**，不是任何一条指令的内部地址；'
    '② **63 / 65** 满足「VA 恰等于前一条线性解码指令的**终点**」（`gap == prev_size`），即它们坐在指令**边界之后**，'
    '余下 2 条（`0x708d59` gap 3 > prev_size 2、`0x7b0085` gap 3 > prev_size 2）连边界都不贴；'
    '③ 换读法「从 VA-k（k<=7）重解一条指令能否覆盖 VA」得 **48** 条命中、**17** 条连这个也覆盖不到'
    '（两条读法命中数 0 vs 48，**不可互换**）；'
    '④ 「位移 1..7」的真身是 **VA 相对前一条起点的距离**分布 **1:22 2:20 3:14 4:1 5:1 6:6 7:1**（与 R163 记录逐项相同），'
    '它**不是**「在某条指令内部的位移」—— 把距离读成内部位移，会把「解码洞」误当「地址对齐问题」。'
    '⇒ 正确措辞是：**`bounds` = `.text` 内、VirtualSize 以内的线性解码起点集，另含 65 个「1 字节重对齐点」**；'
    '**不得**写成「65 条指令内位移」，也**不得**据此推出「生成器把指令内部地址也收进来了」。'
    '另记一条口径边界（本轮实测）：skipdata 的**分块**扫描得 1,392,706 条，与 `bounds` 既不互相包含'
    '（多 188、缺 74，假差合计 262）⇒ 「skipdata 起点序列 == `bounds`」这条判据**只能**用 R164 的**整段一次扫**，'
    '分块版会造出假差。本条**计数一字未改**（1,392,592 / 1,392,527 / 65 / 1,593 全部原值）。'
)


print('== 0 前置：V545 基线 ==')
b545 = rb(V545)
ck('A0 V545 sha256 == 5707594f…', hashlib.sha256(b545).hexdigest() == V545_SHA,
   hashlib.sha256(b545).hexdigest()[:16])
ck('A1 V545 字节 == 104,017', len(b545) == V545_BYTES, len(b545))
ck('A2 V545 CR == 0（全 LF）', b545.count(b'\r') == 0, b545.count(b'\r'))

txt = b545.decode('utf-8')
lines = txt.split('\n')
if lines and lines[-1] == '':
    lines = lines[:-1]
ck('A3 V545 行数 == 55（表头 + 54 事实）', len(lines) == 55, len(lines))
rows = [l.split('\t') for l in lines]
# S-530（自错，本轮当场抓出）：首版写 new = list(rows) —— 那是**浅拷贝**，改 new 里某行的第 5 列
# 同时改了 rows 里的同一个 list 对象 ⇒ 差分基准被就地污染，drift 恒为空、B4/B6 假 FAIL。
# 正确做法是对每行做独立拷贝（深一层即可，行内是 str 不可变）。
rows_base = [list(r) for r in rows]
ck('A4 每行 5 列', all(len(r) == 5 for r in rows), {len(r) for r in rows})

d = dict((r[0], r) for r in rows[1:])
ck('A5 F24 存在', 'F24' in d, sorted(d)[:3])
ck('A6 F24 limits 里尚无 R166 补段（幂等前提）', 'R166 补·那 65 条' not in d['F24'][4],
   d['F24'][4].count('R166 补·那 65 条'))

print('\n== 1 追加（只动 F24 第 5 列）==')
new = list(rows)
for r in new:
    if r[0] == 'F24':
        r[4] = r[4] + APPEND
out_txt = '\n'.join('\t'.join(r) for r in new) + '\n'
out_b = out_txt.encode('utf-8')
h = hashlib.sha256(out_b).hexdigest()
print('  V546 = %d B / sha256 %s' % (len(out_b), h))
ck('B0 新件字节 > 旧件（纯追加）', len(out_b) > len(b545), (len(out_b), len(b545)))
ck('B1 新件 CR == 0', out_b.count(b'\r') == 0, out_b.count(b'\r'))
ck('B2 行数仍 55', len(out_txt.rstrip('\n').split('\n')) == 55,
   len(out_txt.rstrip('\n').split('\n')))
ck('B3 F24 statement / grade / evidence 三列逐字节不变',
   new[[r[0] for r in new].index('F24')][1:4] == rows_base[[r[0] for r in rows_base].index('F24')][1:4],
   len(new[[r[0] for r in new].index('F24')][1]))
drift = [a[0] for a, b in zip(rows_base, new) if a != b]
ck('B4 差分行恰 1 行且是 F24（整文件逐行差分，不靠行号）', drift == ['F24'], drift)
cell = 0
for a, b in zip(rows_base, new):
    for i in range(5):
        if a[i] != b[i]:
            cell += 1
            ck('B5 唯一变化单元是 F24 的第 5 列', a[0] == 'F24' and i == 4, (a[0], i))
ck('B6 变化单元恰好 1 个', cell == 1, cell)

print('\n== 2 落盘（wx 独占备份 -> 写 -> 回读）==')
if os.path.exists(V546) and rb(V546) == out_b:
    ck('C0 幂等：V546 已是终态', True, V546)
else:
    if not os.path.isdir(V546D):
        os.makedirs(V546D)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bakp = os.path.join(BD, 'FACT_INDEX_V545.before_r166d_%s.bak' % stamp)
    fd = os.open(bakp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(b545)
    ck('C1 备份已 wx 独占创建且与 V545 逐字节相同', rb(bakp) == b545, os.path.basename(bakp))
    with open(V546, 'wb') as f:
        f.write(out_b)
    ck('C2 回读 V546 sha256 与内存一致', hashlib.sha256(rb(V546)).hexdigest() == h,
       hashlib.sha256(rb(V546)).hexdigest()[:16])

b546 = rb(V546)
ck('C3 V545 一字未改（写后复查）', hashlib.sha256(b545).hexdigest() == V545_SHA,
   hashlib.sha256(rb(V545)).hexdigest()[:16])
ck('C4 V546 落盘字节 = %d' % len(out_b), len(b546) == len(out_b), len(b546))

json.dump({'v545_sha': V545_SHA, 'v545_bytes': V545_BYTES,
           'v546_sha': h, 'v546_bytes': len(out_b),
           'append_bytes': len(APPEND.encode('utf-8')),
           'append_chars': len(APPEND),
           'drift': drift, 'cells': cell,
           'asserts': RES, 'fails': FAILS},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), len(FAILS), OUT))
if FAILS:
    print('FAILS: %s' % FAILS)
sys.exit(1 if FAILS else 0)
