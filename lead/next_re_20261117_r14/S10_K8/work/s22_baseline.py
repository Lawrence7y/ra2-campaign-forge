from pathlib import Path
import csv,re
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv';ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
def rows(p):
 with p.open('r',encoding='utf-8',newline='') as f:yield from csv.DictReader(f,delimiter='\t')
def norm(x):return x.strip().lower()
def named(r):
 n=r.get('name','').strip();return bool(n) and not n.startswith('sub_') and '::sub_' not in n and re.search(r'::(?:v?slot)\d+$',n) is None
for sub in ['S10','S22']:
 cov=[r for r in rows(COV) if r.get('subsystem','').strip().upper()==sub]
 atl={norm(r['entry']) for r in rows(ATL)};ci=[r for r in cov if norm(r['entry']) in atl]
 p=sum(r['grade'].strip().upper()=='[已证]' for r in ci)
 print(sub,'rows',len(cov),'atlas',len(ci),'proved',p,'pct',f'{100*p/len(ci):.4f}','named',sum(named(r) for r in ci))
