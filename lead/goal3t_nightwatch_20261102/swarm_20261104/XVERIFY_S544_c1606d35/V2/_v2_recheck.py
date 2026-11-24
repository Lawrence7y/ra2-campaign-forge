# -*- coding: utf-8 -*-
"""复核员-V2 独立复算。

铁律：只读原始 json / 源码；不读 V2 的 _v2_data.json / _v2_meta.json /
_v2_*_out.txt（避免把被复核件的中间产物当原始数据）。
全部 python 以 `python -I -X utf8` 运行，路径全为绝对路径。
"""
import glob
import json
import os
import math
import datetime
import hashlib
import statistics
import collections
import re

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
ROOT = r'D:/Project/ra2-campaign-forge'
V2 = ROOT + r'/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V2'
HARNESS_V4 = ROOT + r'/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py'
HARNESS3 = ROOT + r'/lead/qc151_harness_merge_20261021/qc151_trip.harness3.py'
TZ8 = datetime.timezone(datetime.timedelta(hours=8))
V4 = '38244d2907e7f7fa'


def pearson(xs, ys):
    n = len(xs)
    assert n == len(ys) and n >= 2
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return (sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else None), n


def ts8(a):
    try:
        return datetime.datetime.fromtimestamp(a, TZ8).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


# ============ 从原始 json 重建全库（不采信任何中间产物） ============
files = sorted(glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True))
rows = []
for p in files:
    d = json.load(open(p, encoding='utf-8'))
    tripdir = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    if tripdir == '.':
        tripdir = '(TRIP_ROOT)'
    e = d.get('frame_edges') or []
    f0 = f1 = t0 = t1 = df = dt = live = None
    if len(e) >= 2:
        f0, t0 = e[0][0], e[0][1]
        f1, t1 = e[-1][0], e[-1][1]
        df, dt = f1 - f0, t1 - t0
        if dt > 0:
            live = df / dt
    g = d.get('gate') or {}
    st = d.get('stats') or {}
    sm = d.get('samples') or {}
    rows.append(dict(
        path=p.replace('\\', '/'), rel=os.path.relpath(p, T).replace('\\', '/'),
        tripdir=tripdir, trip_id=d.get('trip_id'), window=d.get('window'),
        keys=sorted(d.keys()), schema=d.get('schema'),
        time8=ts8(d.get('t_abs0')), t_abs0=d.get('t_abs0'),
        map_sha256=d.get('map_sha256'), gamemd_sha256=d.get('gamemd_sha256'),
        t_clock=d.get('t_clock'), hz=d.get('hz'), span_s=d.get('span_s'),
        settle_s=d.get('settle_s'),
        units0=g.get('units0'), pre=g.get('pre_fps15'), gate_ok=g.get('ok'),
        f0=f0, f1=f1, df=df, dt=dt, live=live,
        fps_avg=st.get('fps_avg'), fps_p50=st.get('fps_p50'),
        max_stall_s=st.get('max_stall_s'), n_edges=len(e),
        n_samples=len(sm.get('t') or []),
        s_t0=(sm.get('t') or [None])[0], s_t1=(sm.get('t') or [None])[-1],
        s_f0=(sm.get('f') or [None])[0], s_f1=(sm.get('f') or [None])[-1],
        verdict=d.get('verdict'), error=d.get('error'),
    ))

# ============ 版本：只读原始 _launch_result.json / qc151_fields.json ============
launch = {}
for p in sorted(glob.glob(os.path.join(T, '**', '_launch_result.json'), recursive=True)):
    dirn = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    d = json.load(open(p, encoding='utf-8'))
    a = d.get('argv') or []
    tgt = None
    for i, s in enumerate(a):
        if s == '--target-sha256' and i + 1 < len(a):
            tgt = a[i + 1]
    launch[dirn] = dict(sha16=d.get('harness_sha16'), harness=d.get('harness'),
                        arg0=a[0] if a else None, target=tgt, rc=d.get('rc'))

fields = {}
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    dirn = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    try:
        fl = json.load(open(p, encoding='utf-8'))
    except Exception:
        fl = []
    start = None
    tss = []
    rect = set()
    tz = set()
    harness_mentions = set()
    for e in fl:
        if not isinstance(e, dict):
            continue
        if e.get('key') == 'h7_measure_start_frame':
            start = e.get('value')
        if e.get('ts'):
            tss.append(str(e['ts']))
        for k, v in e.items():
            s = str(v)
            if 'window_stable_rect' in k:
                rect.add(s)
            if re.search(r'\+08:00|\+0800', s):
                tz.add('+08:00')
            if re.search(r'harness\d*(_v\d+)?\.py', s, re.I):
                harness_mentions.add(s[:160])
    fields[dirn] = dict(start=start, n=len(fl), ts_min=min(tss) if tss else None,
                        ts_max=max(tss) if tss else None, tz=sorted(tz),
                        rect=sorted(rect), hm=sorted(harness_mentions))

for x in rows:
    m = launch.get(x['tripdir'], {})
    x['sha16'] = m.get('sha16')
    x['hlabel'] = os.path.basename(m['arg0']) if m.get('arg0') else None
    x['arg0'] = m.get('arg0')
    x['target_sha'] = m.get('target')
    f = fields.get(x['tripdir'], {})
    x['start_frame'] = f.get('start')
    x['has_launch'] = x['tripdir'] in launch

print('=== 0. 全库普查（从 103 份原始 measure_w*.json 重建）===')
print('  measure_w*.json 总数 =', len(rows))
print('  趟目录数(按 dirname 计) =', len(set(x['tripdir'] for x in rows)))
print('  live_fps 可算(len(frame_edges)>=2 且 dt>0) =', sum(1 for x in rows if x['live'] is not None))
print('  units0 非空 =', sum(1 for x in rows if x['units0'] is not None))
print('  units0>0 =', sum(1 for x in rows if x['units0'] and x['units0'] > 0))
print('  units0 与 live_fps 同时可算 =', sum(1 for x in rows if x['units0'] is not None and x['live'] is not None))
print('  顶层键普查：')
allk = collections.Counter(k for x in rows for k in x['keys'])
for k in sorted(allk):
    print('    %-18s %d' % (k, allk[k]))
print('  含 harness_sha16 的 json 数 =', sum(1 for x in rows if 'harness_sha16' in x['keys']))
print('  含 argv 的 json 数 =', sum(1 for x in rows if 'argv' in x['keys']))
print('  schema distinct =', sorted(set(str(x['schema']) for x in rows)))
print('  _launch_result.json 份数 =', len(launch), ' 其中带 sha16 =', sum(1 for v in launch.values() if v['sha16']))
print('  无 _launch_result.json 的趟目录数 =', len(set(x['tripdir'] for x in rows) - set(launch)))
print('  qc151_fields.json 份数 =', len(fields),
      ' 含 harness*.py 字样的 value 命中数 =', sum(1 for v in fields.values() if v['hm']))
print('  gamemd_sha256 distinct =', len(set(x['gamemd_sha256'] for x in rows)),
      sorted(set(x['gamemd_sha256'] for x in rows)))
print('  map_sha256 distinct =', len(set(x['map_sha256'] for x in rows)))
print('  t_clock distinct =', sorted(set(str(x['t_clock']) for x in rows)))
print('  hz distinct =', sorted(set(str(x['hz']) for x in rows)))
print('  qc151_fields ts 全 +08:00 ?',
      all(('+08:00' in v['tz']) or not v['ts_min'] for v in fields.values()),
      ' 有 ts 的文件数 =', sum(1 for v in fields.values() if v['ts_min']))

print()
print('=== 1. [V2-A1] §544 点名四时刻：逐窗从原始 frame_edges 重算 ===')
KEY = ['2026-11-01 16:48', '2026-11-03 11:20', '2026-10-21 19:03', '2026-10-31 20:15']
named = []
for k in KEY:
    L = sorted([x for x in rows if x['time8'] and x['time8'].startswith(k)], key=lambda y: y['window'])
    print('  --', k, '窗数', len(L))
    for x in L:
        named.append(x)
        print('     %s w%s  f %s→%s  Δf=%s  Δt=%.6f  live=%.6f  units0=%s  pre=%s  fps_avg=%.6f  max_stall=%s  sha16=%s  hlabel=%s' % (
            x['time8'], x['window'], x['f0'], x['f1'], x['df'], x['dt'],
            x['live'], x['units0'], x['pre'], x['fps_avg'], x['max_stall_s'],
            x['sha16'], x['hlabel']))
        print('        map=%s  start_frame=%s  samples_t=%.6f..%.6f  n_samples=%s' % (
            x['map_sha256'][:16], x['start_frame'], x['s_t0'], x['s_t1'], x['n_samples']))
# 「同负载」检验
u = [x['units0'] for x in named]
fast_u = [1225, 1189]
slow_u = [881, 1347]
print('  四组 units0 =', u)
print('  快组均值 = %.4f  慢组均值 = %.4f  绝对差 = %.4f  相对快组 = %.4f%%' % (
    sum(fast_u) / 2, sum(slow_u) / 2, abs(sum(fast_u) / 2 - sum(slow_u) / 2),
    100 * abs(sum(fast_u) / 2 - sum(slow_u) / 2) / (sum(fast_u) / 2)))
print('  10-21 19:03 的 units0=881 ∈ [1180,1360] ?', 1180 <= 881 <= 1360)
print('  四窗 |fps_avg - live_fps| =', ['%.6f' % abs(x['fps_avg'] - x['live']) for x in named])
print('  四窗 Δt 范围 = %.6f .. %.6f' % (min(x['dt'] for x in named), max(x['dt'] for x in named)))

print()
print('=== 2. [V2-A2] 对标带 units0∈[1180,1360] 快/慢 × v4/非v4 ===')
band = [x for x in rows if x['units0'] and 1180 <= x['units0'] <= 1360
        and x['live'] is not None and x['live'] > 0]
fast = [x for x in band if x['live'] >= 28]
slow = [x for x in band if x['live'] < 15]
mid = [x for x in band if 15 <= x['live'] < 28]
print('  band n=%d fast(>=28)=%d mid=%d slow(<15)=%d  (mid 被 2x2 丢弃)' % (len(band), len(fast), len(mid), len(slow)))
for lab, L in [('FAST', fast), ('MID', mid), ('SLOW', slow)]:
    c = collections.Counter((str(x['sha16']), str(x['hlabel'])) for x in L)
    print('  %-5s n=%-3d trips=%s  %s' % (lab, len(L), sorted(set(x['tripdir'] for x in L)), dict(c)))
a = sum(1 for x in fast if x['sha16'] == V4)
b = len(fast) - a
c = sum(1 for x in slow if x['sha16'] == V4)
d = len(slow) - c
den = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
phi = (a * d - b * c) / den if den else float('nan')
print('  2x2: fast_v4=%d fast_nonv4=%d slow_v4=%d slow_nonv4=%d  phi=%+.6f' % (a, b, c, d, phi))
# 趟级（去重复计数）φ
def trip_class(L):
    g = collections.defaultdict(list)
    for x in L:
        g[x['tripdir']].append(x)
    return g
tf = trip_class(fast)
tsl = trip_class(slow)
at = sum(1 for k, L in tf.items() if any(x['sha16'] == V4 for x in L))
bt = len(tf) - at
ct = sum(1 for k, L in tsl.items() if any(x['sha16'] == V4 for x in L))
dt_ = len(tsl) - ct
dent = math.sqrt((at + bt) * (ct + dt_) * (at + ct) * (bt + dt_))
phit = (at * dt_ - bt * ct) / dent if dent else float('nan')
print('  趟级 2x2(去同趟多窗重复): fast_trips_v4=%d fast_trips_nonv4=%d slow_trips_v4=%d slow_trips_nonv4=%d  phi=%+.6f  n_trips=%d' % (
    at, bt, ct, dt_, phit, len(tf) + len(tsl)))
# 全库扩展口径 units0>=800
sub = [x for x in rows if x['units0'] and x['units0'] >= 800 and x['live'] is not None and x['live'] > 0]
fa = [x for x in sub if x['live'] >= 28]
sl = [x for x in sub if x['live'] < 15]
A = sum(1 for x in fa if x['sha16'] == V4); B = len(fa) - A
C = sum(1 for x in sl if x['sha16'] == V4); D = len(sl) - C
den2 = math.sqrt((A + B) * (C + D) * (A + C) * (B + D))
phi2 = (A * D - B * C) / den2 if den2 else float('nan')
print('  放宽到 units0>=800: n=%d fast=%d slow=%d  2x2=(%d,%d,%d,%d) phi=%+.6f' % (
    len(sub), len(fa), len(sl), A, B, C, D, phi2))
print('  FAST 非 v4 反例:', sorted(set((x['tripdir'], str(x['sha16']), str(x['hlabel']), x['units0'], '%.3f' % x['live']) for x in fa if x['sha16'] != V4)))
# 版本内反例：同一 v4 版本内 fps 极差
v4all = [x for x in rows if x['sha16'] == V4 and x['live'] and x['live'] > 0]
print('  v4 全库窗 n=%d live=%.3f..%.3f 极差=%.3f' % (
    len(v4all), min(x['live'] for x in v4all), max(x['live'] for x in v4all),
    max(x['live'] for x in v4all) - min(x['live'] for x in v4all)))
for dd in ['l3_1101v4c']:
    L = sorted([x for x in rows if x['tripdir'] == dd and x['live']], key=lambda y: y['window'])
    print('  同 v4 单趟 %s: %s  极差=%.4f' % (dd, ['%.3f' % x['live'] for x in L],
                                          max(x['live'] for x in L) - min(x['live'] for x in L)))
# 「跨日期 + 又快又慢」同 units0 档
g = collections.defaultdict(list)
for x in rows:
    if x['units0'] is not None and x['live'] is not None and x['live'] > 0:
        g[x['units0']].append(x)
found = 0
for uu in sorted(g):
    L = g[uu]
    dates = sorted(set(x['time8'][:10] for x in L if x['time8']))
    if len(dates) > 1:
        lv = [x['live'] for x in L]
        print('  跨日期档 units0=%-6s n=%-3d dates=%s live=%.3f..%.3f harness=%s' % (
            uu, len(L), dates, min(lv), max(lv), sorted(set(str(x['hlabel']) for x in L))))
        if max(lv) >= 28 and min(lv) < 15:
            found += 1
print('  具有「跨日期 + 又快又慢」的 units0 档数量 =', found)
# 出现>=3 次的档
cnt = collections.Counter(x['units0'] for x in rows if x['units0'] is not None)
print('  出现>=3 次的 units0 档 =', sorted(k for k, v in cnt.items() if v >= 3))

print()
print('=== 3. [V2-A2] map / 母本 / 相位 / 版本来源（原始文件） ===')
for dd in ['l1c_20261021', 'l3_20261021', 'l3_20261031ha', 'l3_20261031hb',
           'l3_1101v3a', 'l3_1101v3b', 'l3_1101v4c', 'l3_1101v4d', 'l3_1101v4e']:
    L = sorted([x for x in rows if x['tripdir'] == dd], key=lambda y: y['window'])
    m = launch.get(dd, {})
    print('  %-18s has_launch=%-5s sha16=%-18s hlabel=%-28s start_frame=%-5s map=%s target=%s' % (
        dd, dd in launch, str(m.get('sha16')), str(os.path.basename(m['arg0']) if m.get('arg0') else None),
        str(fields.get(dd, {}).get('start')), L[0]['map_sha256'][:16], str(m.get('target'))[:16]))
print('  h7_measure_start_frame 取值分布 =', collections.Counter(str(v['start']) for v in fields.values()))
print('  无 launch 的趟目录 =', sorted(set(x['tripdir'] for x in rows) - set(launch)))
# 独立 hashlib 复算 sha16
print('  --- 独立 hashlib 复算现存 harness 文件 sha256[:16] ---')
for p in [HARNESS_V4, HARNESS3,
          ROOT + r'/lead/goal1_harness8_20261031/qc151_trip.harness8.py',
          ROOT + r'/lead/goal1_harness8_20261031/qc151_trip.harness8_v3.py']:
    if os.path.isfile(p):
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
        print('    %-70s %s' % (os.path.basename(p), h))
    else:
        print('    MISSING', p)

print()
print('=== 4. [V2-A3] 自实现 Pearson：全库 / 变体 / 去重复计数 ===')
valid = [x for x in rows if x['units0'] is not None and x['live'] is not None
         and x['live'] > 0 and x['pre'] is not None]
print('  valid(units0非空 & live>0 & pre非空) n=%d 独立趟=%d' % (len(valid), len(set(x['tripdir'] for x in valid))))
for tag, xs, ys in [
    ('rho(pre,live)  全库', [x['pre'] for x in valid], [x['live'] for x in valid]),
    ('rho(units0,live) 全库', [float(x['units0']) for x in valid], [x['live'] for x in valid]),
    ('rho(pre,units0) 全库', [x['pre'] for x in valid], [float(x['units0']) for x in valid]),
]:
    r, n = pearson(xs, ys)
    print('  %-32s n=%-3d rho=%+.6f' % (tag, n, r))
pos = [x for x in valid if x['units0'] > 0]
r, n = pearson([x['pre'] for x in pos], [x['live'] for x in pos])
print('  rho(pre,live) units0>0            n=%-3d rho=%+.6f  (§544 的 +0.8925 复现?)' % (n, r))
r2, n2 = pearson([float(x['units0']) for x in pos], [x['live'] for x in pos])
print('  rho(units0,live) units0>0         n=%-3d rho=%+.6f' % (n2, r2))
ge = [x for x in valid if x['units0'] >= 800]
r, n = pearson([x['pre'] for x in ge], [x['live'] for x in ge])
print('  rho(pre,live) units0>=800         n=%-3d rho=%+.6f' % (n, r))
print('  被 units0>0 排除的窗 =', [(x['tripdir'], x['window'], x['units0'], x['pre'], '%.3f' % x['live']) for x in valid if not x['units0'] > 0])
# 固定 harness 版本内
byh = collections.defaultdict(list)
for x in valid:
    byh[x['sha16'] or ('LABEL:' + str(x['hlabel']))].append(x)
print('  --- 固定 harness 版本内 rho(units0,live) ---')
for k in sorted(byh, key=str):
    L = byh[k]
    if len(L) < 3:
        print('    %-40s n=%d SKIP' % (str(k), len(L)))
        continue
    r, n = pearson([float(y['units0']) for y in L], [y['live'] for y in L])
    print('    %-40s n=%-3d trips=%-2d rho=%s' % (str(k), n, len(set(y['tripdir'] for y in L)),
                                                 ('%+.6f' % r) if r is not None else 'UNDEF'))
xx, yy = [], []
for k, L in byh.items():
    if len(L) < 2:
        continue
    mu = sum(y['units0'] for y in L) / len(L)
    mv = sum(y['live'] for y in L) / len(L)
    for y in L:
        xx.append(y['units0'] - mu); yy.append(y['live'] - mv)
r, n = pearson(xx, yy)
print('  pooled within-harness (demeaned) n=%d rho=%+.6f' % (n, r))
# 同义反复：pre 每趟是否恒定
bytrip = collections.defaultdict(list)
for x in valid:
    bytrip[x['tripdir']].append(x)
multi = {k: L for k, L in bytrip.items() if len(L) >= 2}
same = sum(1 for k, L in multi.items() if len(set(y['pre'] for y in L)) == 1)
print('  多窗趟数=%d  其中 pre_fps15 全窗相同=%d  (独立 pre 值总数=%d / 窗数=%d)' % (
    len(multi), same, len(set((x['tripdir'], x['pre']) for x in valid)), len(valid)))
print('  反例(趟内 pre 不同):', [(k, [y['pre'] for y in L]) for k, L in multi.items() if len(set(y['pre'] for y in L)) != 1])
tx = [sum(y['pre'] for y in L) / len(L) for L in bytrip.values()]
ty = [sum(y['live'] for y in L) / len(L) for L in bytrip.values()]
tu = [sum(y['units0'] for y in L) / len(L) for L in bytrip.values()]
r, n = pearson(tx, ty)
print('  rho(pre,live) 按趟取均值(去重复计数) n=%d rho=%+.6f' % (n, r))
r, n = pearson(tu, ty)
print('  rho(units0,live) 按趟取均值          n=%d rho=%+.6f' % (n, r))
diffs = [abs(x['live'] - x['pre']) for x in valid]
print('  |live - pre| 中位数 = %.4f 均值 = %.4f' % (statistics.median(diffs), sum(diffs) / len(diffs)))
# 趟内 vs 趟间
within = []
for k, L in sorted(bytrip.items()):
    lv = [y['live'] for y in L if y['live'] and y['live'] > 0]
    if len(lv) >= 2:
        within.append((k, max(lv) - min(lv)))
print('  趟内极差 中位数=%.4f 均值=%.4f max=%.4f (n=%d 趟)' % (
    statistics.median([w[1] for w in within]), sum(w[1] for w in within) / len(within),
    max(w[1] for w in within), len(within)))
means = [sum(y['live'] for y in L if y['live'] and y['live'] > 0) /
         len([y for y in L if y['live'] and y['live'] > 0]) for L in bytrip.values()
         if any(y['live'] and y['live'] > 0 for y in L)]
pairs = [abs(a - b) for i, a in enumerate(means) for b in means[i + 1:]]
print('  趟均值 n=%d 范围 %.3f..%.3f 极差=%.3f 中位数=%.3f' % (
    len(means), min(means), max(means), max(means) - min(means), statistics.median(means)))
print('  两趟均值|差|中位数 = %.4f (n=%d 对)' % (statistics.median(pairs), len(pairs)))
print('  趟间/趟内 比值 = %.4f' % (statistics.median(pairs) / statistics.median([w[1] for w in within])))

print()
print('=== 5. [V2 §7] 停摆尾段稀释：archive_T34 与四组对照 ===')
for pat in ['archive_T34/measure_w0.json']:
    p = os.path.join(T, pat)
    if os.path.isfile(p):
        d = json.load(open(p, encoding='utf-8'))
        e = d.get('frame_edges') or []
        st = d.get('stats') or {}
        print('  %s: n_edges=%d fps_avg=%s fps_p50=%s max_stall_s=%s span_s=%s' % (
            pat, len(e), st.get('fps_avg'), st.get('fps_p50'), st.get('max_stall_s'), d.get('span_s')))
        sm = d.get('samples') or {}
        tt = sm.get('t') or []
        gaps = sum(t2 - t1 for t1, t2 in zip(tt, tt[1:]) if t2 - t1 > 0.010)
        print('    samples.t 相邻 dt>10ms 累计缺口 = %.6f s (n_samples=%d, t=%.3f..%.3f)' % (
            gaps, len(tt), tt[0], tt[-1]))
print('  四组对照窗尾段: Δt/span_s 分别 =',
      ['%.4f' % (x['dt'] / x['span_s']) for x in named])

print()
print('=== 6. 源码定义（pre_fps15 / fps_avg / _measure_poll_span）===')
for path, pats in [
    (HARNESS_V4, [r'MEASURE_GATE_SPAN_S', r'MEASURE_SETTLE_S', r'pre_fps15',
                  r'fps_avg', r'def _measure_poll_span', r'def _measure_stats',
                  r'_rpm_u32', r'time\.perf_counter', r'gate_pts', r's_samples']),
]:
    print('  FILE', path)
    lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    for pat in pats:
        hits = [(i + 1, l.strip()[:150]) for i, l in enumerate(lines) if re.search(pat, l)]
        print('    PAT %-28s hits=%d  %s' % (pat, len(hits), hits[:6]))
