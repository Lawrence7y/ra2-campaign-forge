# -*- coding: utf-8 -*-
"""复核员-V2 第三轮：元数据字段按 key/value 精确取值 + MANIFEST 结构。"""
import glob, json, os, collections, hashlib

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

print('=== A. qc151_fields.json 的 window_stable_rect（按 e["key"] 精确匹配）===')
rect = collections.Counter()
tzs = collections.Counter()
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    try:
        fl = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    for e in fl:
        if not isinstance(e, dict):
            continue
        k = str(e.get('key'))
        v = e.get('value')
        if 'window_stable_rect' in k or 'stable_rect' in k:
            rect[str(v)] += 1
        if e.get('ts'):
            tzs[str(e['ts'])[-6:]] += 1
print('  window_stable_rect 值分布 =', dict(rect))
print('  ts 尾 6 字符分布（时区）=', dict(tzs))
print('  样例字段键名（取一份文件前 30 个 key）：')
p1 = sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True))[0]
fl = json.load(open(p1, encoding='utf-8'))
print('   ', p1)
print('   ', [e.get('key') for e in fl if isinstance(e, dict)][:30])

print()
print('=== B. MANIFEST.json 结构 ===')
mp = os.path.join(T, 'MANIFEST.json')
mj = json.load(open(mp, encoding='utf-8'))
print('  顶层键 =', list(mj.keys()) if isinstance(mj, dict) else type(mj))
if isinstance(mj, dict):
    for k, v in mj.items():
        print('   %-30s type=%-8s len=%s' % (k, type(v).__name__, len(v) if hasattr(v, '__len__') else '-'))
        if isinstance(v, list) and v:
            print('      首元素:', str(v[0])[:180])
        elif isinstance(v, dict):
            print('      键数:', len(v), '样例:', str(list(v.items())[:1])[:180])
s = open(mp, encoding='utf-8').read()
print('  "sha256" 字面出现次数 =', s.count('sha256'))

print()
print('=== C. carrier_creation_receipt.json 键数分布 + 快慢趟 ===')
cc = collections.Counter()
for p in sorted(glob.glob(os.path.join(T, '**', 'carrier_creation_receipt.json'), recursive=True)):
    try:
        d = json.load(open(p, encoding='utf-8'))
        cc[len(d)] += 1
    except Exception:
        pass
print('  全部 =', dict(cc))
for dd in ['l3_1101v4d', 'l3_1101v4e', 'l1c_20261021', 'l3_20261031hb', 't55k_20261020']:
    p = os.path.join(T, dd, 'carrier_creation_receipt.json')
    if os.path.isfile(p):
        print('  %-20s 键数=%d' % (dd, len(json.load(open(p, encoding='utf-8')))))
    else:
        print('  %-20s MISSING' % dd)

print()
print('=== D. 快慢趟 _launch_result.json 的 --target-sha256 与 json map_sha256 一致性 ===')
for dd in ['l1c_20261021', 'l3_20261021', 'l3_20261031hb', 'l3_1101v4d', 'l3_1101v4e']:
    lp = os.path.join(T, dd, '_launch_result.json')
    jp = os.path.join(T, dd, 'measure_w0.json')
    if not (os.path.isfile(lp) and os.path.isfile(jp)):
        continue
    ld = json.load(open(lp, encoding='utf-8'))
    jd = json.load(open(jp, encoding='utf-8'))
    a = ld.get('argv') or []
    tgt = a[a.index('--target-sha256') + 1] if '--target-sha256' in a else None
    print('  %-20s target=%s  map=%s  MATCH=%s' % (
        dd, str(tgt)[:16], str(jd.get('map_sha256'))[:16], tgt == jd.get('map_sha256')))

print()
print('=== E. v4 趟内漂移：l3_1101v4c 三窗原始 frame_edges 首末 ===')
for w in range(3):
    p = os.path.join(T, 'l3_1101v4c', 'measure_w%d.json' % w)
    if os.path.isfile(p):
        j = json.load(open(p, encoding='utf-8'))
        e = j['frame_edges']
        l = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1])
        print('  w%d f %s→%s Δt=%.6f live=%.4f  gate.pre=%s units0=%s' % (
            w, e[0][0], e[-1][0], e[-1][1] - e[0][1], l,
            (j.get('gate') or {}).get('pre_fps15'), (j.get('gate') or {}).get('units0')))

print()
print('=== F. 早期 harness7 快趟核对（fast 非 v4 反例的原始数据）===')
for dd in ['l3_20261023q', 'l3_20261023r', 't55k_20261020']:
    lp = os.path.join(T, dd, '_launch_result.json')
    sha = None
    if os.path.isfile(lp):
        sha = json.load(open(lp, encoding='utf-8')).get('harness_sha16')
    for w in range(3):
        p = os.path.join(T, dd, 'measure_w%d.json' % w)
        if not os.path.isfile(p):
            continue
        j = json.load(open(p, encoding='utf-8'))
        e = j.get('frame_edges') or []
        l = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1]) if len(e) >= 2 and e[-1][1] > e[0][1] else None
        print('  %-18s sha16=%-18s w%d units0=%-6s live=%s' % (
            dd, str(sha), w, (j.get('gate') or {}).get('units0'),
            ('%.4f' % l) if l is not None else 'N/A'))
