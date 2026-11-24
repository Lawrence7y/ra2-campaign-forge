import sys,csv,re,collections
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
with ATL.open(encoding='utf-8-sig',newline='') as f: atl={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
# all proved functions with semantic names matching keywords (any subsystem)
KEY=re.compile(r'ammo|weapon|target|threat|range|veter|experien|promot|deploy|unload|repair|reload|best|fire|attack|damage|upgrade|rank|elite|score|kill|crate|heal|occup',re.I)
rows=[]
for k,r in cov.items():
    if r['grade'].strip()!='[已证]':continue
    blob=(r['name']+' '+r['one_line_semantics'])
    if KEY.search(blob): rows.append((k,r['subsystem'],r['name'],r['one_line_semantics']))
rows.sort()
print('PROVED_KEYWORD_COUNT',len(rows))
for x in rows: print('\t'.join(x))
