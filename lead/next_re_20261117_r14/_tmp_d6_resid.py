import sys

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

def named_r14(n):
    """R14-R14: name non-empty, not start with sub_, and not Class::sub_"""
    if not n or n.startswith('sub_'):
        return False
    if '::sub_' in n:
        return False
    return True

def named_strict(n):
    if not named_r14(n):
        return False
    tail = n.split('::')[-1]
    if tail.startswith('slot') or tail.startswith('vslot'):
        return False
    return True

want = sys.argv[1] if len(sys.argv) > 1 else 'S16'
rows = []
for e, sz in atlas.items():
    r = cov.get(e.upper())
    if not r or r[1].strip() != want:
        continue
    rows.append((e.upper(), sz, r[2].strip(), r[4].strip(), r[3].strip()[:70]))

n = len(rows)
nr = sum(1 for x in rows if named_r14(x[2]))
ns = sum(1 for x in rows if named_strict(x[2]))
pv = sum(1 for x in rows if x[3] == '[\u5df2\u8bc1]')
print('%s atlas_n=%d named_R14=%d (%.2f%%) need=%d gap=%d | named_strict=%d | proved=%d (%.2f%%) need=%d'
      % (want, n, nr, nr * 100.0 / n, -(-n * 9 // 10), -(-n * 9 // 10) - nr,
         ns, pv, pv * 100.0 / n, -(-n // 2)))
print('--- residual under R14 (no name) ---')
for x in rows:
    if not named_r14(x[2]):
        print('  %s size=%-5s %-14s %-28s %s' % (x[0], x[1], x[3], x[2], x[4]))
