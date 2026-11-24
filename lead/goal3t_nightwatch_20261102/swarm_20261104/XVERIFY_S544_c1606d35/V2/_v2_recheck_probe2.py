# -*- coding: utf-8 -*-
"""复核员-V2 第二轮：针对 REPORT.md 中可疑计数/口径的定点复核。"""
import glob, json, os, math, collections, hashlib, re

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
ROOT = r'D:/Project/ra2-campaign-forge'
V4 = '38244d2907e7f7fa'

print('=== A. _launch_result.json 带/不带 sha16 的确切份数（REPORT 说 24 带 / 4 不带）===')
ps = sorted(glob.glob(os.path.join(T, '**', '_launch_result.json'), recursive=True))
print('  全库份数 =', len(ps))
no_sha = []
for p in ps:
    d = json.load(open(p, encoding='utf-8'))
    if not d.get('harness_sha16'):
        no_sha.append(os.path.relpath(os.path.dirname(p), T).replace('\\', '/'))
print('  无 sha16 份数 =', len(no_sha), '目录 =', no_sha)
print('  有 sha16 份数 =', len(ps) - len(no_sha))

print()
print('=== B. 无 _launch_result.json 的趟目录确切数量（REPORT 说 15 个）===')
mdirs = sorted(set(os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
                   for p in glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True)))
ldirs = set(os.path.relpath(os.path.dirname(p), T).replace('\\', '/') for p in ps)
missing = sorted(set(mdirs) - ldirs)
print('  有 measure_w*.json 的趟目录数 =', len(mdirs))
print('  无 launch 的趟目录数 =', len(missing))
print('  ', missing)
arch = [d for d in missing if d.startswith('archive_T')]
print('  其中 archive_T* =', len(arch), arch)

print()
print('=== C. 「30 个多窗 trip」说法核对 ===')
bydir = collections.defaultdict(list)
for p in sorted(glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True)):
    d = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    j = json.load(open(p, encoding='utf-8'))
    bydir[d].append((j.get('window'), (j.get('gate') or {}).get('pre_fps15')))
multi = {d: L for d, L in bydir.items() if len(L) >= 2}
print('  全库多窗(>=2 份 measure_w)趟数 =', len(multi))
same = sum(1 for d, L in multi.items() if len(set(x[1] for x in L)) == 1)
print('  其中 pre_fps15 全窗相同 =', same, '/', len(multi))
print('  pre 不相同者 =', [(d, L) for d, L in multi.items() if len(set(x[1] for x in L)) != 1][:10])
# 在 valid 子集（units0非空 & live>0 & pre非空）
def live(j):
    e = j.get('frame_edges') or []
    if len(e) < 2:
        return None
    dt = e[-1][1] - e[0][1]
    return (e[-1][0] - e[0][0]) / dt if dt > 0 else None
valid_bydir = collections.defaultdict(list)
for p in sorted(glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True)):
    d = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    j = json.load(open(p, encoding='utf-8'))
    g = j.get('gate') or {}
    lv = live(j)
    if g.get('units0') is not None and lv is not None and lv > 0 and g.get('pre_fps15') is not None:
        valid_bydir[d].append(g['pre_fps15'])
vmulti = {d: L for d, L in valid_bydir.items() if len(L) >= 2}
print('  valid 子集多窗趟数 =', len(vmulti), ' 独立趟总数 =', len(valid_bydir),
      ' 窗总数 =', sum(len(L) for L in valid_bydir.values()))
print('  valid 多窗 pre 全相同 =', sum(1 for L in vmulti.values() if len(set(L)) == 1), '/', len(vmulti))

print()
print('=== D. φ 对切分点的敏感性（REPORT 只报 >=28 / <15，丢掉 2 个 MID 窗）===')
rows = []
for p in sorted(glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True)):
    j = json.load(open(p, encoding='utf-8'))
    d = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    g = j.get('gate') or {}
    lv = live(j)
    lp = os.path.join(T, d, '_launch_result.json') if d != '.' else None
    sha = None
    if lp and os.path.isfile(lp):
        sha = json.load(open(lp, encoding='utf-8')).get('harness_sha16')
    rows.append((d, g.get('units0'), lv, sha))
band = [r for r in rows if r[1] and 1180 <= r[1] <= 1360 and r[2] and r[2] > 0]
print('  band n =', len(band))
for fcut, scut in [(28, 15), (28, 28), (30, 15), (25, 15), (20, 20)]:
    fa = [r for r in band if r[2] >= fcut]
    sl = [r for r in band if r[2] < scut]
    a = sum(1 for r in fa if r[3] == V4); b = len(fa) - a
    c = sum(1 for r in sl if r[3] == V4); d_ = len(sl) - c
    den = math.sqrt((a + b) * (c + d_) * (a + c) * (b + d_))
    phi = (a * d_ - b * c) / den if den else float('nan')
    print('  fast>=%-3s slow<%-3s : n_used=%2d (band-n_dropped=%2d)  2x2=(%d,%d,%d,%d) phi=%+.6f' % (
        fcut, scut, len(fa) + len(sl), len(band) - len(fa) - len(sl), a, b, c, d_, phi))
mid = [(r[0], '%.3f' % r[2], r[3]) for r in band if 15 <= r[2] < 28]
print('  被 2x2 丢弃的 MID 窗 =', mid)
print('  注意：MID 中含 v4 窗？', any(r[3] == V4 for r in band if 15 <= r[2] < 28))

print()
print('=== E. h7_measure_start_frame 全部非 None 值（REPORT 说只有 400/800）===')
cnt = collections.Counter()
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    try:
        fl = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    v = [e.get('value') for e in fl if isinstance(e, dict) and e.get('key') == 'h7_measure_start_frame']
    cnt[str(v[0] if v else None)] += 1
    if v and v[0] not in (None, 400, 800):
        print('  非 400/800 值:', os.path.relpath(os.path.dirname(p), T).replace('\\', '/'), v)
print('  分布 =', dict(cnt))
# 这些 1200/800 趟有没有 measure_w*.json
for dd in ['l3_1101v3c', 'l3_1101v4a', 'l3_1101v4b']:
    n = len(glob.glob(os.path.join(T, dd, 'measure_w*.json')))
    print('  %s measure_w*.json 数=%d' % (dd, n))

print()
print('=== F. 载体件数 / MANIFEST 条目 / tz（A2 keyFacts）===')
mp = os.path.join(T, 'MANIFEST.json')
if os.path.isfile(mp):
    s = open(mp, encoding='utf-8').read()
    print('  MANIFEST.json 中 "sha256" 字面出现次数 =', s.count('sha256'))
    try:
        mj = json.loads(s)
        print('  MANIFEST.json 顶层类型 =', type(mj).__name__, ' 条目数 =', len(mj))
        if isinstance(mj, dict):
            vals = [v for v in mj.values() if isinstance(v, str) and len(v) == 64]
            print('  值为 64 位哈希的条目数 =', len(vals))
    except Exception as e:
        print('  json 解析失败', e)
cr = glob.glob(os.path.join(T, '**', 'carrier_creation_receipt.json'), recursive=True)
print('  carrier_creation_receipt.json 份数 =', len(cr))
kc = collections.Counter()
for p in cr:
    try:
        kc[len(json.load(open(p, encoding='utf-8')))] += 1
    except Exception:
        pass
print('  其顶层键数分布 =', dict(kc))
# tz
tz = collections.Counter()
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    try:
        fl = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    for e in fl:
        if isinstance(e, dict):
            for k, v in e.items():
                for m in re.findall(r'[+-]\d{2}:?\d{2}', str(v)):
                    tz[m] += 1
print('  qc151_fields.json 中所有 ±HH:MM 字面量 =', dict(tz))
# window_stable_rect
rect = collections.Counter()
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    try:
        fl = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    for e in fl:
        if isinstance(e, dict):
            for k, v in e.items():
                if 'window_stable_rect' in k:
                    rect[str(v)] += 1
print('  window_stable_rect 分布 =', dict(rect))

print()
print('=== G. REPORT §7 「差 <0.06」核对 ===')
for dd, w in [('l3_1101v4d', 0), ('l3_1101v4e', 0), ('l3_1101v4e', 1),
              ('l1c_20261021', 0), ('l3_20261031hb', 0), ('l3_20261031hb', 1)]:
    p = os.path.join(T, dd, 'measure_w%d.json' % w)
    j = json.load(open(p, encoding='utf-8'))
    e = j['frame_edges']
    l = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1])
    a = j['stats']['fps_avg']
    print('  %-18s w%d |fps_avg-live| = %.6f  %s' % (dd, w, abs(a - l), '<0.06' if abs(a - l) < 0.06 else '>=0.06'))

print()
print('=== H. harness3.py 现存文件 sha16（REPORT 说 5c56dac5c17a2ba）===')
h3 = os.path.join(T, 'qc151_harness_merge_20261021', 'qc151_trip.harness3.py')
print('  路径存在 =', os.path.isfile(h3))
if os.path.isfile(h3):
    print('  sha256[:16] =', hashlib.sha256(open(h3, 'rb').read()).hexdigest()[:16])
