import json
import glob
import os
from pathlib import Path

BASE = Path('out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip')

dirs = []
for pat in ('archive_*', '../qc161_t1*_run_20261017/raw', '../qc161_t1*_verify_20261017/raw'):
    dirs.extend(glob.glob(str(BASE / pat)))

rows = []
for d in dirs:
    f = os.path.join(d, 'qc151_fields.json')
    if not os.path.isfile(f):
        continue
    try:
        o = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(o, list):
        continue
    fs = None
    stages = {}
    for r in o:
        if not isinstance(r, dict):
            continue
        if r.get('group') == 'META' and r.get('key') == 'fullscreen':
            fs = r.get('value')
        if r.get('group') == 'BUDGET' and str(r.get('key', '')).startswith('stage_seconds:'):
            stages[r['key'].split(':', 1)[1]] = r.get('value')
    if fs is not None:
        continue
    total = sum(v for v in stages.values() if isinstance(v, (int, float)))
    rows.append((os.path.basename(os.path.normpath(d)), total, len(stages),
                 stages.get('frame'), stages.get('nav')))

rows.sort(key=lambda r: -r[1])
print("窗口模式趟（stage_seconds 求和）: 共 %d" % len(rows))
print("%-24s %-9s %-4s %-9s %s" % ('trip', 'sum_s', 'n', 'frame_s', 'nav_s'))
for r in rows[:15]:
    print("%-24s %-9.2f %-4d %-9s %s" % r)
if rows:
    mx = max(r[1] for r in rows)
    print()
    print("max sum = %.2f s" % mx)
    print("超 180s:", [(r[0], round(r[1], 1)) for r in rows if r[1] > 180])
