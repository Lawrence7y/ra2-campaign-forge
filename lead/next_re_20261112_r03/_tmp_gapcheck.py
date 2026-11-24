import csv
import sys

p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W20_combat\out\tickcost.csv'
rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
bad = [r for r in rows if r['interval_ms'] and float(r['interval_ms']) >= 64.0]
print('rows with interval>=64ms:', len(bad))
for r in bad:
    print({k: r[k] for k in ('idx', 't_rel_s', 'interval_ms', 'cyc_est_ms', 'frame', 'mode', 'fg', 'df', 'gap', 'hiccup', 'note')})
print('--- last 5 rows ---')
for r in rows[-5:]:
    print({k: r[k] for k in ('idx', 't_rel_s', 'interval_ms', 'cyc_est_ms', 'frame', 'mode', 'A8ED50', 'note')})
print('--- first row with frame>0 ---')
for r in rows:
    if int(r['frame']) > 0:
        print({k: r[k] for k in ('idx', 't_rel_s', 'interval_ms', 'cyc_est_ms', 'frame', 'mode')})
        break
