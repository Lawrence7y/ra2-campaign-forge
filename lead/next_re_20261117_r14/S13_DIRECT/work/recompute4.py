import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
from collections import Counter
cov=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
txt=open(cov,'r',encoding='utf-8',errors='replace').read()
rows=[ln.split(chr(9)) for ln in txt.split(chr(10))[1:] if ln.strip() and len(ln.split(chr(9)))>=8]
atl=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
atlset=set()
for ln in open(atl,'r',encoding='utf-8',errors='replace').read().split(chr(10))[1:]:
    if ln.strip(): atlset.add(ln.split(chr(9))[0].lower().strip())
# S13 all coverage rows regardless atlas
s13all=[r for r in rows if r[1].strip().upper()=='S13']
print('S13 all coverage rows',len(s13all),dict(Counter(r[4].strip() for r in s13all)))
s13in=[r for r in s13all if r[0].lower().strip() in atlset]
s13out=[r for r in s13all if r[0].lower().strip() not in atlset]
print('S13 in atlas',len(s13in),dict(Counter(r[4].strip() for r in s13in)))
print('S13 NOT in atlas',len(s13out),dict(Counter(r[4].strip() for r in s13out)))
# the 3 K12 audit rows
for e in ['0040F870','0054E890','0054EA70']:
    m=[r for r in rows if r[0].upper()==e]
    print(e, [(r[1],r[2],r[4]) for r in m])
