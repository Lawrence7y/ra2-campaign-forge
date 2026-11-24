# -*- coding: utf-8 -*-
# N16-4: full-population scan of measure_w*.json under qc161 root (recursive).
# Classify zero-progress windows (logic_frames==0) with f0 != 0 -> the "32" denominator set.
import os, json, glob

ROOT = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

all_files = sorted(glob.glob(os.path.join(ROOT, '**', 'measure_w*.json'), recursive=True))
print('total measure_w*.json =', len(all_files))

zero_total = 0
zero_f0ne0 = 0
rows = []
for p in all_files:
    rel = os.path.relpath(p, ROOT).replace('\\', '/')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            m = json.load(f)
    except Exception as e:
        rows.append((rel, 'LOAD_ERR', repr(e)))
        continue
    samples = m.get('samples') or {}
    fl = samples.get('f') or []
    if not fl:
        rows.append((rel, 'NO_SAMPLES', ''))
        continue
    f0 = fl[0]; fmin = min(fl); fmax = max(fl)
    st = m.get('stats') or {}
    lf = st.get('logic_frames'); note = st.get('note')
    if lf == 0:
        zero_total += 1
        tag = 'ZERO_f0ne0' if f0 != 0 else 'ZERO_f0eq0'
        if f0 != 0:
            zero_f0ne0 += 1
        rows.append((rel, tag, 'f0=%s fmin=%s fmax=%s lf=%s' % (f0, fmin, fmax, lf)))
    else:
        rows.append((rel, 'advancing', 'f0=%s lf=%s' % (f0, lf)))

print('zero-progress total =', zero_total)
print('zero-progress f0!=0 =', zero_f0ne0)
print()
for rel, tag, info in rows:
    if tag in ('ZERO_f0ne0', 'ZERO_f0eq0', 'LOAD_ERR', 'NO_SAMPLES'):
        print(tag, rel, info)
