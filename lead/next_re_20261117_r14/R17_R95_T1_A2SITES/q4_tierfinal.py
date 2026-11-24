"""Q2/Q4 second axis: does BYTES survive the (defensible) reading that only the calls section
counts? -> must be re-expressed at the tier_final byte level, and the membership file must exist."""
import csv, io
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P = BASE + r'\R17_R88_T1_SEMDEF\tier_final.tsv'
LOG=[]
def L(*a):
    s=' '.join(str(x) for x in a); LOG.append(s); print(s, flush=True)
raw = open(P, 'rb').read()
for enc in ('utf-8','utf-8-sig','gbk'):
    try:
        t = raw.decode(enc); break
    except Exception:
        continue
head = t.splitlines()[0]
L('tier_final.tsv header:', head)
rows = list(csv.DictReader(io.StringIO(t), delimiter='\t'))
L('rows', len(rows))
L('cols', list(rows[0].keys()))
# find byte column
bcol = [c for c in rows[0] if c and ('byte' in c.lower() or 'size' in c.lower() or 'len' in c.lower())]
L('byte-ish cols', bcol)
tot = sum(int(r[bcol[0]]) for r in rows) if bcol else None
L('sum(bytes)=', tot, ' == 744172839 ?', tot == 744172839)
hit = [r for r in rows if 'a2_sites.json' in str(r)]
L('a2_sites rows:', len(hit))
for h in hit:
    L('  ', h)
open(BASE + r'\R17_R95_T1_A2SITES\q4_tierfinal.out','w',encoding='utf-8').write('\n'.join(LOG))
