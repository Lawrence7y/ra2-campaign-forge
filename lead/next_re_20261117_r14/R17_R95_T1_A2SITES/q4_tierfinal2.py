import csv, io
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P = BASE + r'\R17_R88_T1_SEMDEF\tier_final.tsv'
LOG=[]
def L(*a):
    s=' '.join(str(x) for x in a); LOG.append(s); print(s, flush=True)
t = open(P, 'rb').read().decode('utf-8')
# header has 5 cols; check a data line's real field count
lines = t.splitlines()
L('n_lines', len(lines))
L('header', repr(lines[0]))
L('line1  ', repr(lines[1]))
L('a2 line', [l for l in lines if 'a2_sites.json' in l])
rows = list(csv.reader(io.StringIO(t), delimiter='\t'))
L('row lens', sorted(set(len(r) for r in rows)))
# drop malformed
data = [r for r in rows[1:] if len(r) == 5]
L('well-formed rows', len(data))
tot = sum(int(r[1]) for r in data)
L('sum(bytes)', tot, '== 744172839 ?', tot == 744172839)
L('rows with a2_sites', [r for r in data if 'a2_sites.json' in r[0]])
open(BASE + r'\R17_R95_T1_A2SITES\q4_tierfinal.out','w',encoding='utf-8').write('\n'.join(LOG))
