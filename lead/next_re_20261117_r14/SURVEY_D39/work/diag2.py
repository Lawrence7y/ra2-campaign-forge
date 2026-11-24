import csv,collections
from pathlib import Path
p=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
F=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
C=[]
for l in p.read_text(encoding='utf-8-sig').splitlines()[1:]:
 if l.strip():
  q=l.split('\t')+['']*8;C.append(dict(zip(F,q[:8])))
for e in ['0040B640','0040BBC0','00459FF0','004AF610','0040EEC0','0046B5E0']:
 print('\n',e)
 for r in C:
  if r['entry'].strip().upper()==e: print(r['subsystem'],r['grade'],'|',r['name'],'|',r['one_line_semantics'])
