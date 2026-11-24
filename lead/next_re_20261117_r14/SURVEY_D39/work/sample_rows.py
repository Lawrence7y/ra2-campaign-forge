import csv,json,collections
from pathlib import Path
p=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
F=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
rs=[]
for line in p.read_text(encoding='utf-8-sig').splitlines()[1:]:
 if line.strip():
  q=line.split('\t')+['']*8
  rs.append(dict(zip(F,q[:8])))
for s in ['S10','S11','S20','S13']:
 xs=[r for r in rs if r['subsystem']==s and r['grade']=='[静态推断]']
 print('\n',s,len(xs))
 for r in xs[:12]: print(r['entry'],r['name'],'|',r['one_line_semantics'],'|',r['evidence_path'],'|sources',r['n_sources'])
 print('name prefix',collections.Counter(r['name'].split('::')[0] if '::' in r['name'] else '(none)' for r in xs).most_common(8))
 print('sem prefix',collections.Counter(r['one_line_semantics'][:20] for r in xs).most_common(5))
