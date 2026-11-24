# -*- coding: utf-8 -*-
"""M82 phase 1b: inspect analysis detail for edge cases before applying."""
import os, json, collections, re
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
d = json.load(open(os.path.join(R14, 'MERGE_M82', '_analysis_detail.json'), 'r', encoding='utf-8'))
detail = d['detail']

multi = [x for x in detail if len(x['rel_paths']) > 1]
print('=== rows with >1 rel path: count ===', len(multi))

tr = [x for x in detail if 'classification_trace' in x['evidence_path']]
print('=== rows with classification_trace: count ===', len(tr))

wk = [x for x in detail if any(p.startswith('work/') for p in x['rel_paths'])]
print('=== rows with work/: count ===', len(wk))
for x in wk:
    print(' ', x['entry'], x['row_class'], '|', x['evidence_path'], '|', x['candidates'])

uniq = [x for x in detail if x['row_class'] == 'unique']
print('\n=== unique rows: candidate depth histogram ===')
depth = collections.Counter()
for x in uniq:
    for v in x['candidates'].values():
        for c in v:
            depth[len(c.split('/'))] += 1
print(dict(depth))

print('\n=== sample unique rows with mapping ===')
for x in uniq[:8]:
    print(x['entry'], '|', x['evidence_path'])
    for k, v in x['candidates'].items():
        print('      ', k, '=>', v)

print('\n=== multi-part unique rows: card dirs per part ===')
shown = 0
for x in multi:
    if x['row_class'] != 'unique':
        continue
    cands = [v[0] for v in x['candidates'].values() if v]
    carddirs = set('/'.join(c.split('/')[:-1]) for c in cands)
    print(x['entry'], 'cards=', carddirs)
    shown += 1
    if shown >= 15:
        break

print('\n=== unique rows where any part has != 1 candidate ===')
bad = [x for x in uniq if any(len(v) != 1 for v in x['candidates'].values())]
print('count:', len(bad))

print('\n=== unique rows with parts mapping to >1 distinct card dir ===')
mixed = []
for x in uniq:
    cands = [v[0] for v in x['candidates'].values() if v]
    carddirs = set('/'.join(c.split('/')[:-1]) for c in cands)
    if len(carddirs) > 1:
        mixed.append((x['entry'], carddirs, x['evidence_path']))
print('count:', len(mixed))
for m in mixed[:20]:
    print(' ', m)

print('\n=== anchor shapes among unique rows ===')
SPLIT = re.compile(r'[;,|]')
no_hash = [x for x in uniq if '#' not in x['evidence_path']]
print('rows without # :', len(no_hash))
for x in no_hash[:10]:
    print('  ', x['entry'], '|', x['evidence_path'])

mp = [x for x in uniq if len([p for p in SPLIT.split(x['evidence_path']) if p.strip()]) > 1]
print('multi-part unique rows:', len(mp))

print('\n=== how many unique rows have colon-linespec anchor ===')
colon = [x for x in uniq if re.search(r':0x[0-9A-Fa-f]', x['evidence_path'])]
print('count:', len(colon))
for x in colon[:10]:
    print('  ', x['entry'], '|', x['evidence_path'])
