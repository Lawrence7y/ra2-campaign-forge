"""看 disp_stats.tsv 的分布（只读自己的产物）。"""
import sys, collections
sys.dont_write_bytecode = True
P = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_DESIGN_D48\disp_stats.tsv'
rows = []
with open(P, encoding='utf-8') as f:
    hdr = f.readline().rstrip('\n').split('\t')
    for ln in f:
        c = ln.rstrip('\n').split('\t')
        rows.append(dict(zip(hdr, c)))
print('rows', len(rows))
for k in ('n_tables_live', 'n_uniq_entries_live', 'n_sites'):
    hist = collections.Counter(int(r[k]) for r in rows)
    print('\n%s distribution (top 20):' % k)
    for v, n in sorted(hist.items())[:20]:
        print('  %6d : %d disps' % (v, n))
    print('  max', max(hist))

print('\n--- value-unique disps ---')
vu = [r for r in rows if r['unamb_value'] == 'Y']
print('count', len(vu))
for r in vu[:40]:
    print('  disp=%s sites=%s tabs_live=%s uniq=%s entry=%s cov=%s %s'
          % (r['disp_hex'], r['n_sites'], r['n_tables_live'], r['n_uniq_entries_live'],
             r['witness_entry'], r['in_coverage'], r['grade_has4']))

print('\n--- disp magnitude buckets ---')
b = collections.Counter()
for r in rows:
    d = int(r['disp_dec'])
    if d < 0:
        b['neg'] += 1
    elif d == 0:
        b['0'] += 1
    elif d <= 0x40:
        b['1..0x40'] += 1
    elif d <= 0x100:
        b['0x41..0x100'] += 1
    elif d <= 0x400:
        b['0x101..0x400'] += 1
    else:
        b['>0x400'] += 1
print(b)
