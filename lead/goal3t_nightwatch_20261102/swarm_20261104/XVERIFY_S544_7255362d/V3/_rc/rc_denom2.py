"""Targeted census over the real trip trees only (out/.../qc161_u0400_trip + t55* + lead mirror)."""
import json, os, collections, subprocess, re

BASE = 'D:/Project/ra2-campaign-forge/'
lists = []
for pat in [r'out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\measure_w*.json',
            r'lead\qc161_u0400_trip\measure_w*.json']:
    out = subprocess.run(['cmd', '//c', 'dir /s /b ' + pat], shell=True, capture_output=True, text=True)
    got = [l.replace('\\', '/') for l in out.stdout.splitlines() if l.strip()]
    print(pat, '->', len(got))
    lists += got
# t55 dirs anywhere under the CONTINUE_20261003 lead root
root2 = BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead'
t55 = []
for d in sorted(os.listdir(root2)):
    if d.startswith('t55'):
        p = os.path.join(root2, d)
        if os.path.isdir(p):
            t55.append(d)
print('t55* dirs under CONTINUE_20261003/lead:', t55)
for d in t55:
    for dirpath, dn, fn in os.walk(os.path.join(root2, d)):
        for f in fn:
            if re.match(r'measure_w\d+\.json$', f):
                lists.append(os.path.join(dirpath, f).replace('\\', '/'))
print('total files in scope =', len(lists))

verd = collections.Counter()
u0z = []
rows = []
for p in sorted(set(lists)):
    try:
        j = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print('PARSE FAIL', p, e); continue
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
print('verdicts over scope:', dict(verd))
key = collections.Counter((r[2], os.path.basename(os.path.dirname(r[0])), os.path.basename(r[0])) for r in rows)
print('distinct (trip_id,dir,file) =', len(key))
ded = {}
for r in rows:
    ded.setdefault((r[2], os.path.basename(os.path.dirname(r[0])), os.path.basename(r[0])), r)
print('deduped verdicts:', dict(collections.Counter(str(v[1]) for v in ded.values())))
print('files with gate.units0 == 0:', len(u0z))
for p in u0z:
    print('   ', p.replace(BASE, ''))
print('units0==0 AND fmax==0:', [r[0].replace(BASE, '') for r in rows if r[4] == 0 and r[6] == 0])
# where does the lead mirror duplicate?
lead_mirror = [r[0] for r in rows if '/lead/qc161_u0400_trip/' in r[0] and r[0].startswith(BASE + 'lead')]
print('lead-mirror files =', len(lead_mirror))
