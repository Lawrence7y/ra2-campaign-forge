"""Section 5/7 denominators, bounded walk: lead/ + the real trip tree under out/."""
import json, os, collections, re

BASE = 'D:/Project/ra2-campaign-forge/'
files = []
for r in [BASE + 'lead', BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip']:
    for dirpath, dn, fn in os.walk(r):
        for f in fn:
            if re.match(r'measure_w\d+\.json$', f):
                files.append(os.path.join(dirpath, f).replace('\\', '/'))
files = sorted(set(files))
print('ALL measure_w*.json in scope =', len(files))

verd_all, verd_real, verd_mock = collections.Counter(), collections.Counter(), collections.Counter()
sig = collections.Counter()
mocksig = collections.defaultdict(list)
for p in files:
    try:
        j = json.load(open(p, encoding='utf-8'))
    except Exception:
        verd_all['UNREADABLE'] += 1
        continue
    v = str(j.get('verdict'))
    verd_all[v] += 1
    isreal = '/qc161_u0400_trip/' in p or re.search(r'/t55[0-9a-zA-Z_]*/', p)
    (verd_real if isreal else verd_mock)[v] += 1
    g = j.get('gate') or {}
    st = j.get('stats') or {}
    key = (g.get('pre_fps15'), st.get('fps_avg'), g.get('units0'), v)
    if not isreal:
        sig[key] += 1
        mocksig[key].append(p)
print('verdicts ALL:', dict(verd_all))
print('real-tree files:', sum(verd_real.values()), dict(verd_real))
print('mock/replay files:', sum(verd_mock.values()), dict(verd_mock))
print('top identical mock signatures:')
for k, n in sig.most_common(8):
    print('  ', k, 'x', n, '->', [x.replace(BASE, '') for x in mocksig[k][:2]])

croot = BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead'
print('t55* under CONTINUE lead:', [d for d in os.listdir(croot) if d.startswith('t55')])
print('t55* under BASE lead:', [d for d in os.listdir(BASE + 'lead') if d.startswith('t55')])
print('empty trip_id files (mock):', sum(1 for p in files if '/qc161' not in p and not json.load(open(p, encoding='utf-8')).get('trip_id')))
