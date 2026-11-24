"""Recheck section 5 denominators: verdict distribution over all measure_w*.json,
split into 'real trip tree' vs mock/replay dirs."""
import json, os, collections, re

BASE = 'D:/Project/ra2-campaign-forge/'
files = []
for root in ['lead', 'out']:
    for dirpath, dirnames, filenames in os.walk(BASE + root):
        for fn in filenames:
            if re.match(r'measure_w\d+\.json$', fn):
                files.append(os.path.join(dirpath, fn).replace('\\', '/'))
print('total measure_w*.json =', len(files))

verd = collections.Counter()
units0_zero = []
rows = []
for p in files:
    try:
        j = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        verd['PARSE_ERROR'] += 1
        continue
    verd[str(j.get('verdict'))] += 1
    g = j.get('gate') or {}
    if g.get('units0') == 0:
        units0_zero.append(p)
    s = j.get('samples') or {}
    fs = s.get('f') or []
    rows.append((p, j.get('verdict'), j.get('trip_id'), g.get('pre_fps15'), g.get('units0'),
                 (max(fs) if fs else None), len(fs), j.get('span_s'), j.get('window')))
print('verdict distribution (ALL files):', dict(verd))

real = [r for r in rows if '/qc161_u0400_trip/' in r[0] or '/t55' in r[0].split('/')[-2]]
leadmirror = [r for r in real if r[0].startswith(BASE + 'lead/')]
print('real-tree files =', len(real), ' of which under lead/ mirror =', len(leadmirror))
print('real-tree verdicts:', dict(collections.Counter(str(r[1]) for r in real)))
dedup = {}
for r in real:
    dedup.setdefault((r[2], os.path.basename(os.path.dirname(r[0])), os.path.basename(r[0]), r[7]), r)
print('real-tree deduped (trip_id,dir,file,window) =', len(dedup))
print('deduped verdicts:', dict(collections.Counter(str(v[1]) for v in dedup.values())))
print('units0 == 0 files (all tree):', len(units0_zero))
for p in units0_zero:
    print('   ', p.replace(BASE, ''))
print('units0==0 in real tree:', sum(1 for r in real if r[4] == 0))
print('units0==0 AND fmax==0:', [(r[2], r[0].replace(BASE, '')) for r in rows if r[4] == 0 and r[5] == 0])
