# -*- coding: utf-8 -*-
import glob, json, os, collections

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
ps = sorted(glob.glob(os.path.join(T, '**', '_launch_result.json'), recursive=True))
withsha, without = [], []
for p in ps:
    d = json.load(open(p, encoding='utf-8'))
    dirn = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    a = d.get('argv') or []
    (withsha if d.get('harness_sha16') else without).append(
        (dirn, d.get('harness_sha16'), os.path.basename(a[0]) if a else None))
print('total', len(ps), 'with sha16', len(withsha), 'without', len(without))
print('WITHOUT:')
for x in without:
    print('  ', x)
print('WITH sha16 distinct:', collections.Counter(x[1] for x in withsha))

print()
print('=== h7_measure_start_frame 非 None 的趟 ===')
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    try:
        fl = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    v = [e.get('value') for e in fl if isinstance(e, dict) and e.get('key') == 'h7_measure_start_frame']
    if v and v[0] is not None:
        print('  ', os.path.relpath(os.path.dirname(p), T).replace('\\', '/'), v)

print()
print('=== REPORT 声称的 harness3 路径是否存在 ===')
for p in [r'D:/Project/ra2-campaign-forge/lead/qc151_harness_merge_20261021/qc151_trip.harness3.py']:
    print('  ', p, os.path.isfile(p))
print('=== 全仓搜 qc151_trip.harness3.py（限 lead/ 下）===')
for p in glob.glob(r'D:/Project/ra2-campaign-forge/lead/**/qc151_trip.harness3.py', recursive=True):
    print('  ', p)
