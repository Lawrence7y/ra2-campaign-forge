# -*- coding: utf-8 -*-
"""R128p：收口前的全量断言清点 —— 数字从各脚本的 JSON 产物读，不手填。"""
import os, json, glob
ROOT = '/home/t628/projects/ra2-campaign-forge'
rows = []
tot = ok = 0
for p in sorted(glob.glob(os.path.join(ROOT, '_r128', 'r128*.json'))):
    d = json.load(open(p, encoding='utf-8'))
    c = d.get('checks') or []
    n = len(c); k = sum(1 for x in c if x['ok'])
    rows.append({'file': os.path.basename(p), 'n': n, 'pass': k})
    tot += n; ok += k
for r in rows:
    print('  %-34s %3d/%3d %s' % (r['file'], r['pass'], r['n'],
                                  'PASS' if r['pass'] == r['n'] else 'FAIL'))
print('  TOTAL %d/%d' % (ok, tot))
json.dump({'rows': rows, 'total': tot, 'pass': ok}, open(
    os.path.join(ROOT, '_r128', 'r128p_tally.json'), 'w'), ensure_ascii=False, indent=1)
