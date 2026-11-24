import csv,collections,re
from pathlib import Path
p=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
F=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
rs=[]
for l in p.read_text(encoding='utf-8-sig').splitlines()[1:]:
 if not l.strip(): continue
 q=l.split('\t')+['']*8;rs.append(dict(zip(F,q[:8])))
c=collections.Counter()
ex=collections.defaultdict(list)
for r in rs:
 e=r['entry'].strip().upper()
 if r['subsystem'].strip().upper() in ['S10','S11','S20','S13'] and r['grade'].strip()=='[静态推断]':
  c[e]+=1
  if c[e]>1: ex[e].append(r)
print('total static rows',sum(c.values()),'unique',len(c),'dups',sum(v-1 for v in c.values()))
print(sorted([(k,v) for k,v in c.items() if v>1],key=lambda x:-x[1])[:20])
