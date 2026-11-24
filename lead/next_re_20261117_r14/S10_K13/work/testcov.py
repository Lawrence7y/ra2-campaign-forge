import csv
from pathlib import Path
COV=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
with COV.open(encoding='utf-8',newline='') as f:
 first=f.readline(); print('FIRST',repr(first[:100])); rest=list(f); print('REST0',repr(rest[0][:100]))
 rows=list(csv.DictReader([first.replace(',','\t')]+rest,delimiter='\t'))
 print(len(rows),rows[0])
