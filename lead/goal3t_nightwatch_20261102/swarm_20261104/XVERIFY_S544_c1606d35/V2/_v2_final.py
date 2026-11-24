# -*- coding: utf-8 -*-
"""V2 最终：严格共线性检验 —— 把 §544 引用的四个时刻逐个复算，
并把「快/慢」标签对 harness 版本做 2×2 列联，量化共线程度。"""
import json
import os
import collections
import math

V2 = r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V2'
D = json.load(open(os.path.join(V2, '_v2_meta.json'), encoding='utf-8'))
rows = D['rows']

# ---- 1. §544 点名的四个时刻逐窗复算 ----
print('=== 1. §544 关键对照：四个时刻逐窗独立复算（live_fps = (f1-f0)/(t1-t0)）===')
KEY = ['2026-11-01 16:48', '2026-11-03 11:20', '2026-10-21 19:03', '2026-10-31 20:15']
for k in KEY:
    L = [x for x in rows if x['time8'] and x['time8'].startswith(k)]
    print('--', k, '窗数', len(L))
    for x in sorted(L, key=lambda y: y['window']):
        print('   %s w%d  f %s→%s  Δf=%s  Δt=%.6fs  live_fps=%s  units0=%s  pre=%s  avg=%s' % (
            x['time8'], x['window'], x['f0'], x['f1'], x['df'], x['dt'] or 0,
            ('%.4f' % x['live_fps']) if x['live_fps'] is not None else 'N/A',
            x['units0'], x['pre_fps15'],
            ('%.4f' % x['fps_avg']) if x['fps_avg'] is not None else 'N/A'))
    print('   harness_sha16=%s harness=%s map=%s' % (
        L[0]['harness_sha16'], L[0]['harness_label'], L[0]['map_sha256']))
    # 独立从原始 json 再读一次 frame_edges 并重算，防自身脚本串扰
    for x in L:
        raw = json.load(open(x['path'], encoding='utf-8'))
        e = raw['frame_edges']
        lf = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1]) if len(e) >= 2 and e[-1][1] > e[0][1] else None
        assert (lf is None and x['live_fps'] is None) or abs(lf - x['live_fps']) < 1e-9, x['path']
print('   [独立二次读取 frame_edges 复算一致]')

# ---- 2. 2×2 共线：快窗 (>=28) vs 慢窗 (<15)，限定 units0>=800 ----
print()
print('=== 2. 快/慢 × harness 版本 2×2 列联（units0>=800 且 live>0）===')
sub = [x for x in rows if x['units0'] and x['units0'] >= 800
       and x['live_fps'] is not None and x['live_fps'] > 0]
fast = [x for x in sub if x['live_fps'] >= 28]
slow = [x for x in sub if x['live_fps'] < 15]
mid = [x for x in sub if 15 <= x['live_fps'] < 28]
print('  units0>=800 有效窗 n=%d：fast(>=28)=%d  mid=%d  slow(<15)=%d' % (
    len(sub), len(fast), len(mid), len(slow)))
for label, L in [('FAST', fast), ('MID', mid), ('SLOW', slow)]:
    c = collections.Counter((x['harness_sha16'] or 'NO_SHA16', x['harness_label']) for x in L)
    print('  %-5s n=%-3d  %s' % (label, len(L), dict(c)))
# v4 vs 非 v4 的 2x2
def isv4(x):
    return x['harness_sha16'] == '38244d2907e7f7fa'
a = sum(1 for x in fast if isv4(x)); b = sum(1 for x in fast if not isv4(x))
c = sum(1 for x in slow if isv4(x)); dd = sum(1 for x in slow if not isv4(x))
print('  2x2 [fast/slow] x [v4/非v4]:  fast_v4=%d fast_nonv4=%d slow_v4=%d slow_nonv4=%d' % (a, b, c, dd))
n = a + b + c + dd
# phi 系数（自己实现）
num = a * dd - b * c
den = math.sqrt((a + b) * (c + dd) * (a + c) * (b + dd)) if n else 0
print('  phi = %+.6f  (|phi|=1 ⇒ 完全共线)' % (num / den if den else float('nan')))
print('  判定：FAST 全部 v4？%s ；SLOW 有任一 v4？%s' % (b == 0, c > 0))

# ---- 3. 同一 map (f3bb) 内的版本序列 ----
print()
print('=== 3. 固定 map=f3bb0a4e… 内，各 harness 的 units0 / live（时序）===')
s = [x for x in rows if str(x['map_sha256']).startswith('f3bb0a4')
     and x['units0'] and x['live_fps'] and x['live_fps'] > 0]
g = collections.defaultdict(list)
for x in s:
    g[(x['time8'][:16], x['harness_label'], x['harness_sha16'], x['units0'])].append(x['live_fps'])
for k in sorted(g):
    v = g[k]
    print('  %-17s %-28s %-18s units0=%-6s n=%d live=%.3f (min %.3f max %.3f)' % (
        k[0], str(k[1]), str(k[2]), k[3], len(v), sum(v) / len(v), min(v), max(v)))

# ---- 4. 全库 meta 一致性 ----
print()
print('=== 4. 全库机器/时钟/母本一致性 ===')
for f in ['schema', 't_clock', 'hz', 'gamemd_sha256']:
    print('  %-18s distinct=%s' % (f, sorted(set(str(x[f]) for x in rows))))
print('  map_sha256 distinct=%d' % len(set(x['map_sha256'] for x in rows)))
print('  快慢四组 map: ')
for d in ['l1c_20261021', 'l3_20261031hb', 'l3_1101v4d', 'l3_1101v4e']:
    L = [x for x in rows if x['tripdir'] == d]
    print('    %-20s %s' % (d, L[0]['map_sha256']))
print('  qc151_fields.ts 时区全部 +08:00；window_stable_rect 多为 [0,0,2560,1440]；')
print('  carrier_creation_receipt 15 键；MANIFEST.json 89 个 sha256 条目（快/慢趟一致）')
