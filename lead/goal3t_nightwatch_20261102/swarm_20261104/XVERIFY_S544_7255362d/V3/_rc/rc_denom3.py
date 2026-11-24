"""Targeted census over the real trip trees (no shell): qc161_u0400_trip under both roots + t55*."""
import json, os, collections, re

BASE = 'D:/Project/ra2-campaign-forge/'
roots = [BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip',
         BASE + 'lead/qc161_u0400_trip']
root2 = BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead'
t55 = [os.path.join(root2, d) for d in sorted(os.listdir(root2)) if d.startswith('t55')]
print('t55* dirs:', [os.path.basename(t) for t in t55])
files = []
for r in roots + t55:
    if not os.path.isdir(r):
        print('MISSING ROOT', r)
        continue
    for dirpath, dn, fn in os.walk(r):
        for f in fn:
            if re.match(r'measure_w\d+\.json$', f):
                files.append(os.path.join(dirpath, f).replace('\\', '/'))
print('files in scope =', len(files))

verd = collections.Counter()
u0z, rows = [], []
for p in sorted(set(files)):
    j = json.load(open(p, encoding='utf-8'))
    verd[str(j.get('verdict'))] += 1
    g = j.get('gate') or {}
    s = j.get('samples') or {}
    fs = s.get('f') or []
    cnts = j.get('counters') or []
    fu = next((c['units'] for c in cnts if c.get('units') is not None), None)
    rows.append((p, j.get('verdict'), j.get('trip_id'), g.get('pre_fps15'), g.get('units0'),
                 fu, (max(fs) if fs else None), len(fs), j.get('span_s'), j.get('window')))
    if g.get('units0') == 0:
        u0z.append(p)
print('verdict distribution:', dict(verd))
ded = {}
for r in rows:
    ded.setdefault((r[2], os.path.basename(os.path.dirname(r[0])), os.path.basename(r[0])), r)
print('deduped (trip_id,dir,file) =', len(ded), dict(collections.Counter(str(v[1]) for v in ded.values())))
print('files with gate.units0 == 0:', len(u0z))
for p in u0z:
    print('   ', p.replace(BASE, ''))
print('units0==0 AND fmax==0:', [r[0].replace(BASE, '') for r in rows if r[4] == 0 and r[6] == 0])
print('under lead/ mirror:', sum(1 for r in rows if r[0].startswith(BASE + 'lead')))
