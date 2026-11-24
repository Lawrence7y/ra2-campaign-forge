"""Recheck A1: navigation chain field-by-field equality across the three trips.
Independently recomputed from raw qc151_fields.json (no numbers copied from REPORT.md).
"""
import json, collections, sys

ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
DIRS = ['l3_1101v4e', 'l3_1101v4f', 'l3_1101v4g']

data = {}
for d in DIRS:
    rows = json.load(open(ROOT + d + '/qc151_fields.json', encoding='utf-8'))
    data[d] = rows
    print(d, 'rows =', len(rows))

# (group,key) cardinality per trip, distinct pairs
for d in DIRS:
    pairs = [(r['group'], r['key']) for r in data[d]]
    print(d, 'distinct (group,key) =', len(set(pairs)), 'len(list) =', len(pairs))

allpairs = collections.defaultdict(dict)
for d in DIRS:
    for r in data[d]:
        allpairs[r['group']][r['key']] = r['value']

print('distinct groups =', len(allpairs))
print('total distinct (group,key) =', sum(len(v) for v in allpairs.values()))

# per-group counts
gc = {g: len(k) for g, k in sorted(allpairs.items())}
print('group counts:', json.dumps(gc, ensure_ascii=False))

# per-trip group counts
for d in DIRS:
    c = collections.Counter(r['group'] for r in data[d])
    print(d, 'groups:', json.dumps(dict(sorted(c.items())), ensure_ascii=False))

# Which (group,key) exist in some trips but not all
present = {d: set((r['group'], r['key']) for r in data[d]) for d in DIRS}
union = set().union(*present.values())
print('union size =', len(union))
for d in DIRS:
    print(d, 'missing from union =', len(union - present[d]))
print('keys only in v4e:', sorted(union - present['l3_1101v4f'] - present['l3_1101v4g']))

# value equality across trips for keys present in all three
diff = []
for (g, k) in sorted(union):
    vals = {}
    for d in DIRS:
        if (g, k) in present[d]:
            vals[d] = next(r['value'] for r in data[d] if r['group'] == g and r['key'] == k)
    if len(vals) == 3 and len(set(map(lambda x: json.dumps(x, sort_keys=True), vals.values()))) > 1:
        diff.append((g, k, vals))
print('keys present in all 3 with differing value =', len(diff))
for g, k, vals in diff:
    print('  DIFF', g, '|', k, '=>', {d: str(vals[d])[:80] for d in DIRS})

# NAV group dump for the three trips
print('\n=== NAV group, all keys, three trips ===')
navkeys = sorted(allpairs.get('NAV', {}))
for k in navkeys:
    vals = []
    for d in DIRS:
        v = next((r['value'] for r in data[d] if r['group'] == 'NAV' and r['key'] == k), 'ABSENT')
        vals.append(json.dumps(v, ensure_ascii=False, sort_keys=True) if not isinstance(v, str) else v)
    same = len(set(vals)) == 1
    print(('EQ ' if same else 'NE '), k, '=>', vals if not same else vals[0][:200])
