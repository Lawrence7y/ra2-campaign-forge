import csv, hashlib, os
cov=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
atl=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
print('COV sha', hashlib.sha256(open(cov,'rb').read()).hexdigest()[:16].upper())
with open(cov,'r',encoding='utf-8',errors='replace') as f:
    lines=f.read().split(chr(10))
print('COV raw lines',len(lines))
print('COV header repr:',repr(lines[0]))
for i in range(1,4): print('COV',i,repr(lines[i]))
print('ATL sha', hashlib.sha256(open(atl,'rb').read()).hexdigest()[:16].upper())
with open(atl,'r',encoding='utf-8',errors='replace') as f:
    al=f.read().split(chr(10))
print('ATL raw lines',len(al))
print('ATL header repr:',repr(al[0]))
for i in range(1,4): print('ATL',i,repr(al[i]))
