import hashlib
cov=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
atl=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
# detect encoding: try gbk
raw=open(cov,'rb').read()
try:
    txt=raw.decode('gbk'); enc='gbk'
except Exception as e:
    txt=raw.decode('utf-8',errors='replace'); enc='utf8-replace'
print('COV encoding',enc)
lines=txt.split(chr(10))
# atlas set
atlset=set()
with open(atl,'r',encoding='utf-8',errors='replace') as f:
    al=f.read().split(chr(10))
for ln in al[1:]:
    if not ln.strip(): continue
    atlset.add(ln.split(chr(9))[0].lower().strip())
print('atlas entries',len(atlset))
# coverage rows
hdr=lines[0].replace(',','\t').split(chr(9))
print('hdr',hdr)
from collections import Counter
rows=[]
for ln in lines[1:]:
    if not ln.strip(): continue
    parts=ln.split(chr(9))
    if len(parts)<8: continue
    rows.append(parts)
print('cov data rows',len(rows))
# S13 atlas∩coverage
s13=[r for r in rows if r[1].strip().upper()=='S13' and r[0].lower().strip() in atlset]
print('S13 atlas-intersect n',len(s13))
gc=Counter(r[4].strip() for r in s13)
print('S13 grade dist',dict(gc))
# full coverage grade dist (all rows)
ga=Counter(r[4].strip() for r in rows)
print('ALL grade dist',dict(ga))
# conflict count
print('conflict=1 total',sum(1 for r in rows if r[7].strip()=='1'))
