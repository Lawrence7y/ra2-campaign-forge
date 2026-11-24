# -*- coding: utf-8 -*-
"""V2 §544: 自实现 Pearson ρ（不调库）+ 趟内/趟间极差 + 同义反复论证数据。"""
import json
import math
import os
import collections
import statistics

V2 = r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V2'
D = json.load(open(os.path.join(V2, '_v2_meta.json'), encoding='utf-8'))
rows = D['rows']


def pearson(xs, ys):
    """自己实现 Pearson 积差相关；不调 numpy/scipy/statistics.correlation。"""
    n = len(xs)
    assert n == len(ys) and n >= 2
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None, n, (mx, my, sxx, syy)
    return sxy / math.sqrt(sxx * syy), n, (mx, my, sxx, syy)


def spearman(xs, ys):
    """自己实现 Spearman（平均秩，含并列），辅助稳健性检查。"""
    def ranks(a):
        idx = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and a[idx[j + 1]] == a[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))[0]


def show(tag, xs, ys, extra=''):
    rho, n, m = pearson(xs, ys)
    sp = spearman(xs, ys)
    print('%-56s n=%-3d rho=%-12s spearman=%-9s %s' % (
        tag, n, ('%+.6f' % rho) if rho is not None else 'UNDEF',
        ('%+.6f' % sp) if sp is not None else 'UNDEF', extra))
    return rho


# ---- 4. 全库相关（units0 非空、live_fps 可算且>0） ----
valid = [x for x in rows if x['units0'] is not None
         and x['live_fps'] is not None and x['live_fps'] > 0
         and x['pre_fps15'] is not None]
print('=== 4. 相关系数（自实现 Pearson；样本 = units0非空 & live_fps可算且>0）===')
print('valid n =', len(valid), ' 独立趟数 =', len(set(x['tripdir'] for x in valid)))
show('ρ(pre_fps15, live_fps) 全库', [x['pre_fps15'] for x in valid], [x['live_fps'] for x in valid])
show('ρ(units0,     live_fps) 全库', [x['units0'] for x in valid], [x['live_fps'] for x in valid])
show('ρ(pre_fps15, units0)    全库', [x['pre_fps15'] for x in valid], [float(x['units0']) for x in valid])
show('ρ(pre_fps15, fps_avg)   全库', [x['pre_fps15'] for x in valid],
     [x['fps_avg'] for x in valid if x['fps_avg'] is not None], '(filter fps_avg)')

# 固定 harness 版本内：用 sha16；无 sha16 的用 harness_label 兜底并单列
print()
print('=== 固定 harness 版本内 ρ(units0, live_fps) ===')
byh = collections.defaultdict(list)
for x in valid:
    key = x['harness_sha16'] or ('LABEL:' + str(x['harness_label']))
    byh[key].append(x)
for k in sorted(byh, key=lambda z: str(z)):
    L = byh[k]
    tag = '%-56s' % ('[' + str(k) + '] n=%d trips=%d' % (len(L), len(set(y['tripdir'] for y in L))))
    if len(L) < 3:
        print(tag, 'SKIP(n<3)')
        continue
    show(tag, [y['units0'] for y in L], [y['live_fps'] for y in L])
# 所有"有明确 sha16"的合并分层：每个 sha 内部去均值后再算 pooled within-version rho
print()
print('--- pooled within-version（各组减组均值后合并，消除组间差异）---')
xs, ys = [], []
for k, L in byh.items():
    if len(L) < 2:
        continue
    mu = sum(y['units0'] for y in L) / len(L)
    mv = sum(y['live_fps'] for y in L) / len(L)
    for y in L:
        xs.append(y['units0'] - mu)
        ys.append(y['live_fps'] - mv)
show('ρ(units0, live_fps) pooled within-harness (demeaned)', xs, ys,
     'groups=%d' % sum(1 for L in byh.values() if len(L) >= 2))

# ---- 4b. 只取「同一天同一 harness」的严格对照 ----
print()
print('=== key 对照：同 map(f3bb...) 的六组 harness，各自 units0 / live_fps / pre ===')
strict = [x for x in valid if x['map_sha256'] and x['map_sha256'].startswith('f3bb0a4')]
for h in ['qc151_trip.harness3.py', 'qc151_trip.harness7.py', 'qc151_trip.harness8.py',
          'qc151_trip.harness8_v3.py', 'qc151_trip.harness8_v4.py']:
    L = [x for x in strict if x['harness_label'] == h and 800 <= x['units0'] <= 1400]
    if not L:
        continue
    lv = [y['live_fps'] for y in L]
    print('  %-30s n=%-2d units=%-5s..%-5s live=%6.2f..%6.2f  median=%6.2f  pre=%5.2f..%5.2f' % (
        h, len(L), min(y['units0'] for y in L), max(y['units0'] for y in L),
        min(lv), max(lv), statistics.median(lv),
        min(y['pre_fps15'] for y in L), max(y['pre_fps15'] for y in L)))

# ---- 5. 同义反复：pre_fps15 与 live_fps 的数值关系 ----
print()
print('=== 5. 同义反复检查：pre_fps15 vs live_fps 逐窗比值/差 ===')
diffs = []
for x in sorted(valid, key=lambda y: y['pre_fps15']):
    d = x['live_fps'] - x['pre_fps15']
    diffs.append(abs(d))
    if x['units0'] and 800 <= x['units0'] <= 1400:
        print('  %-20s w%d units=%-5s pre=%7.3f live=%7.3f  Δ=%+7.3f  ratio=%.3f harness=%s' % (
            x['tripdir'], x['window'], x['units0'], x['pre_fps15'], x['live_fps'], d,
            x['live_fps'] / x['pre_fps15'] if x['pre_fps15'] else float('nan'),
            x['harness_label']))
print('  |Δ| 中位数 = %.4f, 均值 = %.4f, n=%d' % (statistics.median(diffs), sum(diffs) / len(diffs), len(diffs)))
# 按 trip 平均后（消除同趟三窗重复计数）
bytrip = collections.defaultdict(list)
for x in valid:
    bytrip[x['tripdir']].append(x)
tx = [sum(y['pre_fps15'] for y in L) / len(L) for L in bytrip.values()]
ty = [sum(y['live_fps'] for y in L) / len(L) for L in bytrip.values()]
tu = [sum(y['units0'] for y in L) / len(L) for L in bytrip.values()]
show('ρ(pre_fps15, live_fps) 按趟取均值（去重复计数）', tx, ty,
     'n_trips=%d' % len(bytrip))
show('ρ(units0, live_fps) 按趟取均值（去重复计数）', tu, ty,
     'n_trips=%d' % len(bytrip))

# ---- 6. 趟内 vs 趟间方差 ----
print()
print('=== 6. 趟内 vs 趟间 fps 极差 ===')
within = []
for d, L in sorted(bytrip.items()):
    lv = [y['live_fps'] for y in L if y['live_fps'] and y['live_fps'] > 0]
    if len(lv) >= 2:
        rg = max(lv) - min(lv)
        within.append((d, len(lv), min(lv), max(lv), rg))
        print('  趟内 %-22s n=%d  %7.3f..%7.3f  极差=%7.3f' % (d, len(lv), min(lv), max(lv), rg))
print('  趟内极差 中位数 = %.4f (n=%d 趟), 均值=%.4f, max=%.4f' % (
    statistics.median([w[4] for w in within]), len(within),
    sum(w[4] for w in within) / len(within), max(w[4] for w in within)))
means = [(d, sum(y['live_fps'] for y in L if y['live_fps'] and y['live_fps'] > 0) /
          len([y for y in L if y['live_fps'] and y['live_fps'] > 0]))
         for d, L in bytrip.items() if any(y['live_fps'] and y['live_fps'] > 0 for y in L)]
vals = [m[1] for m in means]
print('  趟间（各趟均值）n=%d  范围 %.3f..%.3f  极差=%.3f' % (
    len(vals), min(vals), max(vals), max(vals) - min(vals)))
print('  趟间 中位数=%.3f' % statistics.median(vals))
# 趟间极差：所有可能的两趟均值差的中位数
pairs = [abs(a - b) for i, a in enumerate(vals) for b in vals[i + 1:]]
print('  两趟均值 |差| 的中位数 = %.4f (n=%d 对)' % (statistics.median(pairs), len(pairs)))
# 按低/高 units 分组对比
print()
print('  按 units0 分层的趟均值:')
for d, m in sorted(means, key=lambda z: -z[1]):
    L = bytrip[d]
    u = L[0]['units0']
    print('    %-22s units0=%-6s mean_live=%7.3f  harness=%s' % (
        d, u, m, L[0]['harness_label']))
