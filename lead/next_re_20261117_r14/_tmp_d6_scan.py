import os, csv, sys, json

BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
st = os.path.join(BASE, 'CARD_STATUS', 'STATUS.tsv')
rows = list(csv.reader(open(st, encoding='utf-8', errors='replace'), delimiter='\t'))
print('HDR', rows[0])
out = []
for r in rows[1:]:
    if len(r) < 6:
        continue
    card, path, verdict, evid, nline, merged = r[0], r[1], r[2], r[3], r[4], r[5]
    d = os.path.join(BASE, card, 'coverage_delta.tsv')
    n = 0
    if os.path.exists(d):
        lines = [l for l in open(d, encoding='utf-8', errors='replace').read().split('\n') if l.strip()]
        n = max(0, len(lines) - 1)
    if verdict in ('PASS', 'PARTIAL') and n > 0:
        out.append((card, verdict, n, merged))
for o in out:
    print('%-24s %-8s delta=%4d merged=%s' % o)
print('total cards with delta:', len(out))
