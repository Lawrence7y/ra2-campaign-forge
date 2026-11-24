"""
S11-K2 baseline: compute S11 stats from coverage.tsv (authoritative), verify proved count.
Card says 13; PANEL.md says 17 (4.62%). Compute ground truth.
"""
import csv, collections, os

COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
rows = []
with open(COV, encoding='utf-8') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        rows.append(row)

print('total data rows =', len(rows))
# grade distribution whole table
g = collections.Counter(x['grade'] for x in rows)
print('whole grade dist =', dict(g))

s11 = [x for x in rows if x['subsystem'] == 'S11']
print('S11 rows =', len(s11))
g11 = collections.Counter(x['grade'] for x in s11)
print('S11 grade dist =', dict(g11))
print('S11 proved ([已证]) =', g11.get('[已证]', 0))
print('S11 named (not sub_) =', sum(1 for x in s11 if not x['name'].startswith('sub_')))
print('S11 sub_ =', sum(1 for x in s11 if x['name'].startswith('sub_')))

# atlas 分母: entries in function_atlas.tsv
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
atlas = set()
with open(ATLAS, encoding='utf-8') as f:
    head = f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if p:
            atlas.add(p[0].upper().replace('0X','').zfill(8))
print('atlas entries =', len(atlas))
s11_atlas = [x for x in s11 if x['entry'].upper().replace('0X','').zfill(8) in atlas]
print('S11 within atlas =', len(s11_atlas))
print('S11 proved within atlas =', sum(1 for x in s11_atlas if x['grade']=='[已证]'))
print('S11 proved outside atlas =', sum(1 for x in s11 if x['grade']=='[已证]' and x['entry'].upper().replace('0X','').zfill(8) not in atlas))

# list current proved rows
print('\n== current S11 [已证] rows ==')
for x in sorted(s11, key=lambda z: z['entry']):
    if x['grade'] == '[已证]':
        print(x['entry'], x['name'], '|', x['one_line_semantics'][:60], '|', x['evidence_path'])
