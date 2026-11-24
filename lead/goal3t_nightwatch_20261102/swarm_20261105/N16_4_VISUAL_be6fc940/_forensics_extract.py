# -*- coding: utf-8 -*-
# N16-4 step: extract forensics entries referencing measure_w*_end_x.png from qc151_fields*.json
# plus window tail times from measure_w*.json; compare with png mtime.
import os, json, datetime, glob

ROOT = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
DIRS = ['archive_T33','archive_T34','archive_T36','archive_T38','archive_T39',
        'archive_T40','archive_T41','archive_T42','archive_T43','archive_T44',
        'archive_T45','archive_T49_u0800','l1_20261023e4','l3_20261023r']

def fmt_ts(s):
    if not s: return None
    try:
        return datetime.datetime.fromisoformat(s).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    except Exception:
        return s

for sub in DIRS:
    d = os.path.join(ROOT, sub)
    print('='*110)
    print('DIR', sub)
    for cand in ('qc151_fields.json','qc151_fields_post.json'):
        p = os.path.join(d, cand)
        if not os.path.exists(p):
            print('  [%s] MISSING' % cand)
            continue
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data if isinstance(data, list) else []
        for i, item in enumerate(items):
            s = json.dumps(item, ensure_ascii=False)
            if 'measure_w' in s and 'end_x' in s:
                print('  [%s] item%d: %s' % (cand, i, s[:1500]))
    # window tails from measure_w*.json
    for f in sorted(glob.glob(os.path.join(d, 'measure_w*.json'))):
        with open(f, 'r', encoding='utf-8') as g:
            m = json.load(g)
        def find_time(obj, path=''):
            out = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str) and ('T' in v and ':' in v and ('2026' in v or '2025' in v)):
                        out.append((path + '/' + k, v))
                    else:
                        out.extend(find_time(v, path + '/' + k))
            elif isinstance(obj, list):
                for j, v in enumerate(obj):
                    out.extend(find_time(v, path + '/%d' % j))
            return out
        times = find_time(m)
        print('  [%s] time-like fields:' % os.path.basename(f))
        for k, v in times[:12]:
            print('     %s = %s' % (k, v))
        if not times:
            print('     (no time-like strings found)')
