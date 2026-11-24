import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
from collections import Counter
cov=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
txt=open(cov,'r',encoding='utf-8',errors='replace').read()
lines=txt.split(chr(10))
rows=[ln.split(chr(9)) for ln in lines[1:] if ln.strip() and len(ln.split(chr(9)))>=8]
print('ALL grade dist:',dict(Counter(r[4].strip() for r in rows)))
atl=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
atlset=set()
for ln in open(atl,'r',encoding='utf-8',errors='replace').read().split(chr(10))[1:]:
    if ln.strip(): atlset.add(ln.split(chr(9))[0].lower().strip())
s13=[r for r in rows if r[1].strip().upper()=='S13' and r[0].lower().strip() in atlset]
print('S13 n',len(s13))
print('S13 grades',dict(Counter(r[4].strip() for r in s13)))
st=[r for r in s13 if r[4].strip()=='[静态推断]']
print('static',len(st))
# show all 129 static entries with names
for r in st: print(r[0],'|',r[2],'|',r[3])
