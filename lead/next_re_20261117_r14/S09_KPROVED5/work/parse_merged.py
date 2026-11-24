import os
base = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
files = ['S09_KPROVED','S09_KPROVED2','S09_KPROVED3','S09_KPROVED4']
all_entries = []
for d in files:
    p = os.path.join(base, d, 'coverage_delta.tsv')
    entries = []
    with open(p, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0: continue
            line = line.rstrip('\n')
            if not line.strip(): continue
            e = line.split('\t')[0]
            entries.append(e)
    print(d, len(entries), entries)
    all_entries.extend(entries)
print('---')
print('total delta rows', len(all_entries))
print('unique', len(set(all_entries)))
dups = [e for e in set(all_entries) if all_entries.count(e) > 1]
print('dups', sorted(dups))
print('UNIQUE SORTED:')
for e in sorted(set(all_entries)):
    print(e)
