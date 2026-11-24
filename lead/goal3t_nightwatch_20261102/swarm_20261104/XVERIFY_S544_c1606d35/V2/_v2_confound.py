# -*- coding: utf-8 -*-
"""V2: 混淆排查 —— 合并 harness 版本 / 地图 sha / 载体件数 / tz / 机器状态。

harness 来源优先级：
  _launch_result.json 的 harness_sha16 / harness / argv[0]（28 个趟目录有）
  其余趟目录（archive_T*、l1a、t55k、l1_20261023c、TRIP_ROOT 等）用
  qc151_fields.json 的 META.ts 与 measure_w*.json 的 t_abs0 做时间佐证，
  并搜索趟目录内所有含 harness 字样的文件。
"""
import glob
import json
import os
import collections
import re

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
V2 = r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V2'
D = json.load(open(os.path.join(V2, '_v2_data.json'), encoding='utf-8'))
rows = D['rows']

# ---- 1. harvest metadata per trip dir ----
meta = {}
for p in sorted(glob.glob(os.path.join(T, '**', '_launch_result.json'), recursive=True)):
    dirn = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    d = json.load(open(p, encoding='utf-8'))
    a = d.get('argv') or []
    tgt = None
    for i, x in enumerate(a):
        if x == '--target-sha256' and i + 1 < len(a):
            tgt = a[i + 1]
    meta[dirn] = dict(
        sha16=d.get('harness_sha16'),
        harness=d.get('harness'),
        arg0=a[0] if a else None,
        harness_label=os.path.basename(a[0]) if a else None,
        target_sha=tgt,
        rc=d.get('rc'), duration_s=d.get('duration_s'),
        trip_id=d.get('trip_id'),
    )

# qc151_fields META ts + harness mentions
for d in sorted(set(x['tripdir'] for x in rows)):
    real = T if d == '(TRIP_ROOT)' else os.path.join(T, d)
    fp = os.path.join(real, 'qc151_fields.json')
    m = meta.setdefault(d, {})
    if os.path.isfile(fp):
        try:
            fl = json.load(open(fp, encoding='utf-8'))
        except Exception:
            fl = []
        tss = sorted({str(e.get('ts')) for e in fl if isinstance(e, dict) and e.get('ts')})
        m['fields_ts_min'] = tss[0] if tss else None
        m['fields_ts_max'] = tss[-1] if tss else None
        m['fields_n'] = len(fl)
        hits = set()
        for e in fl:
            if isinstance(e, dict):
                for k, v in e.items():
                    s = str(v)
                    if re.search(r'harness\d*(_v\d+)?\.py', s, re.I):
                        hits.add(s[:180])
        m['fields_harness_mentions'] = sorted(hits)[:5]
    else:
        m['fields_ts_min'] = m['fields_ts_max'] = None
    # 趟目录里其它含 harness 的文件名
    hs = []
    for f in glob.glob(os.path.join(real, '**', '*'), recursive=True):
        if 'harness' in os.path.basename(f).lower():
            hs.append(os.path.relpath(f, real).replace('\\', '/'))
    m['harness_named_files'] = sorted(hs)[:8]

# ---- 2. attach to rows ----
for x in rows:
    m = meta.get(x['tripdir'], {})
    x['harness_sha16'] = m.get('sha16')
    x['harness_label'] = m.get('harness_label')
    x['harness_path'] = m.get('harness')
    x['arg0'] = m.get('arg0')
    x['target_sha'] = m.get('target_sha')
    x['fields_ts_min'] = m.get('fields_ts_min')
    x['fields_ts_max'] = m.get('fields_ts_max')
    x['harness_named_files'] = m.get('harness_named_files', [])
    x['fields_harness_mentions'] = m.get('fields_harness_mentions', [])

# ---- 3. map sha census ----
print('=== map_sha256 / gamemd_sha256 全库普查 ===')
for key in ['map_sha256', 'gamemd_sha256', 'schema', 't_clock', 'hz', 'span_s', 'settle_s']:
    c = collections.Counter(x[key] for x in rows)
    print(key, 'distinct=%d' % len(c))
    for k, v in c.most_common(12):
        print('   ', str(k)[:80], v)

# ---- 4. harness label x fast/slow table ----
print()
print('=== 每趟 harness 版本 × 快/慢（按 units0>=1180 的关键对照 + 全库）===')
bytrip = collections.defaultdict(list)
for x in rows:
    bytrip[x['tripdir']].append(x)
print('%-24s %-18s %-28s %-9s %-9s %-8s %-8s' % ('tripdir', 'sha16', 'harness', 'units0', 'time8', 'pre', 'live'))
for d in sorted(bytrip):
    L = sorted(bytrip[d], key=lambda y: (y['t_abs0'] or 0))
    m = L[0]
    lives = [y['live_fps'] for y in L if y['live_fps'] is not None and y['live_fps'] > 0]
    lv = ('%.2f' % (sum(lives) / len(lives))) if lives else 'N/A'
    print('%-24s %-18s %-28s %-9s %-9s %-8s %-8s' % (
        d, str(m['harness_sha16']), str(m['harness_label']),
        str(m['units0']), (m['time8'] or '')[5:16],
        str(m['pre_fps15']), lv))

print()
print('=== 关键对照：units0 1180-1360 的每一窗 ===')
keydirs = set()
for x in rows:
    u = x['units0']
    if u is not None and 1180 <= u <= 1360:
        keydirs.add(x['tripdir'])
for d in sorted(keydirs):
    L = sorted(bytrip[d], key=lambda y: (y['t_abs0'] or 0))
    for y in L:
        print('%-22s %s w%d units0=%-6s live=%-10s pre=%-8s avg=%-8s sha16=%-18s harness=%-24s map=%s' % (
            d, y['time8'], y['window'], y['units0'],
            ('%.4f' % y['live_fps']) if y['live_fps'] is not None else 'N/A',
            y['pre_fps15'],
            ('%.3f' % y['fps_avg']) if y['fps_avg'] is not None else 'N/A',
            str(y['harness_sha16']), str(y['harness_label']), str(y['map_sha256'])[:16]))

print()
print('=== 慢时段(units0 800-1400 且 live<15) vs 快时段(units0 1180-1400 且 live>28) 的 harness 分布 ===')
for label, pred in [('FAST(1180-1400,live>28)', lambda y: y['units0'] and 1180 <= y['units0'] <= 1400 and y['live_fps'] and y['live_fps'] > 28),
                    ('SLOW(800-1400,live<15)', lambda y: y['units0'] and 800 <= y['units0'] <= 1400 and y['live_fps'] and 0 < y['live_fps'] < 15)]:
    sub = [y for y in rows if pred(y)]
    c = collections.Counter((y['harness_sha16'], y['harness_label']) for y in sub)
    print(label, 'n=%d' % len(sub))
    for k, v in c.most_common():
        print('   ', k, v)
    print('   distinct trips:', sorted(set(y['tripdir'] for y in sub)))

json.dump(dict(meta=meta, rows=rows), open(os.path.join(V2, '_v2_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
