"""Dedup the real trip tree properly and check the lead/ mirror identity claim."""
import json, os, collections, re, hashlib

BASE = 'D:/Project/ra2-campaign-forge/'
REAL = [BASE + 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip',
        BASE + 'lead/qc161_u0400_trip',
        BASE + 'lead/t55k_20261020']
files = []
for r in REAL:
    if not os.path.isdir(r):
        print('MISSING', r); continue
    for dp, dn, fn in os.walk(r):
        for f in fn:
            if re.match(r'measure_w\d+\.json$', f):
                files.append(os.path.join(dp, f).replace('\\', '/'))
print('real-tree files =', len(files))
recs = []
for p in sorted(set(files)):
    j = json.load(open(p, encoding='utf-8'))
    rel = p.replace(BASE, '')
    parts = rel.split('/')
    tripdir = parts[-2]
    win = j.get('window')
    recs.append({'path': rel, 'trip_id': j.get('trip_id'), 'dir': tripdir,
                 'file': os.path.basename(p), 'window': win, 'verdict': j.get('verdict'),
                 'sha': hashlib.sha256(open(p, 'rb').read()).hexdigest(),
                 'root': 'out' if rel.startswith('out/') else 'lead'})
print('raw verdict counts:', dict(collections.Counter(str(r['verdict']) for r in recs)))
key = {}
for r in recs:
    key.setdefault((r['trip_id'], r['dir'], r['file'], r['window']), []).append(r)
print('deduped by (trip_id,dir,file,window) =', len(key))
print('deduped verdict counts:', dict(collections.Counter(str(v[0]['verdict']) for v in key.values())))
mirror_pairs = {k: v for k, v in key.items() if len(v) > 1}
print('keys with >1 copy =', len(mirror_pairs))
same_bytes = sum(1 for v in mirror_pairs.values() if len({r['sha'] for r in v}) == 1)
print('  of those, all copies byte-identical =', same_bytes)
for k, v in list(mirror_pairs.items())[:14]:
    print('  ', k[1], k[2], '->', [r['root'] for r in v], 'identical' if len({r['sha'] for r in v}) == 1 else 'DIFFERENT')
print()
print('per-root file counts:', dict(collections.Counter(r['root'] for r in recs)))
