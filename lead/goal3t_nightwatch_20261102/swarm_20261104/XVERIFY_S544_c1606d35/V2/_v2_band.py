# -*- coding: utf-8 -*-
"""V2 补充：① §544 对标负载带内共线性 ② 测量起始帧相位混淆 ③ 「同负载」是否真存在。"""
import json
import os
import math
import collections

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
V2 = r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V2'
D = json.load(open(os.path.join(V2, '_v2_meta.json'), encoding='utf-8'))
rows = D['rows']
V4 = '38244d2907e7f7fa'

# ---- ① §544 对标负载带 1180-1360 的 2x2 ----
print('=== ① §544 对标负载带 units0∈[1180,1360] 的 快/慢 × v4/非v4 ===')
band = [x for x in rows if x['units0'] and 1180 <= x['units0'] <= 1360
        and x['live_fps'] is not None and 0 < x['live_fps']]
fast = [x for x in band if x['live_fps'] >= 28]
slow = [x for x in band if x['live_fps'] < 15]
mid = [x for x in band if 15 <= x['live_fps'] < 28]
print('  band n=%d  fast=%d mid=%d slow=%d' % (len(band), len(fast), len(mid), len(slow)))
for lab, L in [('FAST', fast), ('MID', mid), ('SLOW', slow)]:
    c = collections.Counter((x['harness_sha16'] or 'NO_SHA16', x['harness_label']) for x in L)
    print('  %-5s n=%-3d %s' % (lab, len(L), dict(c)))
    print('        trips:', sorted(set(x['tripdir'] for x in L)))
a = sum(1 for x in fast if x['harness_sha16'] == V4)
b = len(fast) - a
c = sum(1 for x in slow if x['harness_sha16'] == V4)
d = len(slow) - c
print('  2x2: fast_v4=%d fast_nonv4=%d slow_v4=%d slow_nonv4=%d' % (a, b, c, d))
den = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
phi = (a * d - b * c) / den if den else float('nan')
print('  phi = %+.6f  ⇒ 完全共线 = %s' % (phi, abs(phi) == 1.0))
print('  FAST 是否 100%% v4: %s ；SLOW 是否 0%% v4: %s' % (b == 0, c == 0))

# ---- ② 测量起始帧 / h7_measure_start_frame 相位混淆 ----
print()
print('=== ② 相位混淆：每趟首帧号 f0 与 h7_measure_start_frame 配置 ===')
for dd in ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021',
           'l3_20261031ha', 'l3_20261031hb', 'l3_1101v3a', 'l3_1101v3b',
           'l3_1101v4c', 'l3_1101v4d', 'l3_1101v4e', 'l3_20261023q', 'l3_20261023r',
           't55k_20261020', 'l1a_20261020']:
    L = sorted([x for x in rows if x['tripdir'] == dd], key=lambda y: y['window'])
    fp = os.path.join(T, dd, 'qc151_fields.json')
    start = None
    if os.path.isfile(fp):
        for e in json.load(open(fp, encoding='utf-8')):
            if isinstance(e, dict) and e.get('key') == 'h7_measure_start_frame':
                start = e.get('value')
    lv = [x['live_fps'] for x in L if x['live_fps'] and x['live_fps'] > 0]
    print('  %-20s start_frame=%-5s f0(w0)=%-7s units0=%-6s live_w0=%-9s harness=%s' % (
        dd, str(start), str(L[0]['f0']), str(L[0]['units0']),
        ('%.3f' % L[0]['live_fps']) if L[0]['live_fps'] is not None else 'N/A',
        L[0]['harness_label']))

# ---- ③ 「同负载跨时段」是否真存在：同一个 units0 同时有快窗和慢窗？ ----
print()
print('=== ③ 是否存在「完全相同 units0」既快又慢的跨时段对照 ===')
g = collections.defaultdict(list)
for x in rows:
    if x['units0'] is not None and x['live_fps'] is not None and x['live_fps'] > 0:
        g[x['units0']].append(x)
found = 0
for u in sorted(g):
    L = g[u]
    dates = sorted(set(x['time8'][:10] for x in L if x['time8']))
    hs = sorted(set(str(x['harness_label']) for x in L))
    if len(dates) > 1:
        lvs = [x['live_fps'] for x in L]
        print('  units0=%-6s n=%-3d dates=%s harness=%s live=%.3f..%.3f' % (
            u, len(L), dates, hs, min(lvs), max(lvs)))
        if max(lvs) >= 28 and min(lvs) < 15:
            found += 1
print('  具有「跨日期 + 又快又慢」的 units0 档数量 = %d' % found)
print()
print('=== ④ §544 点名四组的 units0 是否「同负载」===')
named = [('11-01 16:48', 1225), ('11-03 11:20', 1189),
         ('10-21 19:03', 881), ('10-31 20:15', 1347)]
for lab, u in named:
    print('  %-14s units0=%s' % (lab, u))
print('  快组 (1225,1189) 差 %d (%.1f%%)；慢组 (881,1347) 差 %d；快组均值 %.1f vs 慢组均值 %.1f 差 %.1f%%' % (
    abs(1225 - 1189), 100 * abs(1225 - 1189) / 1225, abs(881 - 1347),
    (1225 + 1189) / 2, (881 + 1347) / 2,
    100 * abs((1225 + 1189) / 2 - (881 + 1347) / 2) / ((1225 + 1189) / 2)))
print('  10-21 19:03 的 units0=881 是否落在 ask 所述 1180-1360 带内？ %s' % (1180 <= 881 <= 1360))
