import sys,csv
from pathlib import Path
COV=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
with COV.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t'))
for q in ['006FB080','006FCDB0','0065C7E0','0062A4A0','00701900','0070DDD0','00710550','0070D690','006B7BB0']:
 print(q,[ (r['subsystem'],r['grade'],r['name']) for r in rows if r['entry'].lower()==q.lower()])
