import csv, collections

ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'

atlas = {}
with open(ATLAS, newline='', encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 2:
            continue
        atlas[p[0].strip().lower()] = p[1]

cov = {}
with open(COV, newline='', encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 5:
            continue
        cov[p[0].strip().upper()] = p

def is_named_s(n):
    if not n or n.startswith('sub_'):
        return False
    tail = n.split('::')[-1]
    if tail.startswith('sub_') or tail.startswith('slot') or tail.startswith('vslot'):
        return False
    return True

for want in ('S16', 'S17', 'S13', 'S08'):
    rows = []
    for e, sz in atlas.items():
        r = cov.get(e.upper())
        if not r:
            continue
        if r[1].strip() != want:
            continue
        rows.append((e.upper(), sz, r[2].strip(), r[4].strip()))
    unnamed = [x for x in rows if not is_named_s(x[2])]
    print('===', want, 'atlas_n', len(rows), 'unnamed_S', len(unnamed))
    for x in unnamed:
        print('  ', x[0], 'size=' + x[1], '| name=' + x[2], '|', x[3])
