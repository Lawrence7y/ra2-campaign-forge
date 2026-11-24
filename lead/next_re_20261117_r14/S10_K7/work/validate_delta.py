from pathlib import Path
p=Path(__file__).resolve().parent.parent/'coverage_delta.tsv'
rows=[x.split('\t') for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
assert 1<=len(rows)<=2, len(rows)
assert all(len(r)>=6 for r in rows)
assert all(len(r)==8 for r in rows), [len(r) for r in rows]
assert len({r[0] for r in rows})==len(rows)
assert len({r[2] for r in rows})==len(rows)
assert all(r[0]==r[0].upper() for r in rows)
assert all(r[1]=='S10' for r in rows)
assert all(r[4]=='[已证]' for r in rows)
base=p.parent
for r in rows:
 ep=r[5].split('#',1)[0]
 assert (base/ep).exists(), ep
print('DELTA_VALIDATE PASS rows=',len(rows),'entries=',[r[0] for r in rows],'names=',[r[2] for r in rows])
