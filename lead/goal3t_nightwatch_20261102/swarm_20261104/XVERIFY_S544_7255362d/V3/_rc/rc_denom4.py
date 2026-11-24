"""Recompute section 5 denominators with os.walk only (no shell)."""
import json, os, collections, re

BASE = 'D:/Project/ra2-campaign-forge/'
roots = [BASE + 'lead', BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip']
files = []
for r in roots:
    for dirpath, dn, fn in os.walk(r):
        for f in fn:
            if re.match(r'measure_w\d+\.json$', f):
                files.append(os.path.join(dirpath, f).replace('\\', '/'))
print('measure_w*.json under lead + out/qc161_u0400_trip =', len(files))

# also t55* dirs under the CONTINUE root (report counted them as 'real trip tree')
croot = BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead'
t55 = [d for d in sorted(os.listdir(croot)) if d.startswith('t55')]
print('t55* dirs:', t55)
t55files = []
for d in t55:
    for dirpath, dn, fn in os.walk(os.path.join(croot, d)):
        for f in fn:
            if re.match(r'measure_w\d+\.json$', f):
                t55files.append(os.path.join(dirpath, f).replace('\\', '/'))
print('measure files under t55* =', len(t55files))

allf = sorted(set(files + t55files))
verd = collections.Counter()
u0z, fmz, rows = [], [], []
for p in allf:
    try:
        j = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        verd['UNREADABLE'] += 1
        continue
    verd[str(j.get('verdict'))] += 1
    g = j.get('gate') or {}
    fs = (j.get('samples') or {}).get('f') or []
    rows.append((p, j.get('verdict'), j.get('trip_id'), g.get('pre_fps15'), g.get('units0'),
                 max(fs) if fs else None, len(fs), j.get('span_s'), j.get('window')))
    if g.get('units0') == 0:
        u0z.append(p)
    if g.get('units0') == 0 and fs and max(fs) == 0:
        fmz.append(p)
print('total files parsed =', len(allf))
print('verdict distribution:', dict(verd))

real = [r for r in rows if '/qc161_u0400_trip/' in r[0] or '/t55' in r[0]]
print('real-trip-tree files =', len(real))
print('  verdicts:', dict(collections.Counter(str(r[1]) for r in real)))
ded = {}
for r in real:
    ded.setdefault((r[2], os.path.basename(os.path.dirname(r[0])), os.path.basename(r[0]), r[8]), r)
print('  deduped by (trip_id,dir,file,window) =', len(ded))
print('  deduped verdicts:', dict(collections.Counter(str(v[1]) for v in ded.values())))
print('  mirror copies under lead/ =', sum(1 for r in real if r[0].startswith(BASE + 'lead/')))
mock = [r for r in rows if r not in real]
print('non-real-tree files =', len(mock), dict(collections.Counter(str(r[1]) for r in mock)))
print('empty trip_id among non-real =', sum(1 for r in mock if not r[2]))
print('gate.units0 == 0 (ALL) =', len(u0z))
for p in u0z:
    print('   ', p.replace(BASE, ''))
print('units0==0 in real tree =', sum(1 for r in real if r[4] == 0))
print('units0==0 AND fmax==0 =', [p.replace(BASE, '') for p in fmz])
