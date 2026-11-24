import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
idx={}
for ln in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\all_direct_call_sites.tsv',encoding='utf-8').read().split(chr(10))[1:]:
    if not ln.strip(): continue
    p=ln.split()
    idx.setdefault(p[1],[]).append(p[0])
cnt=0
for ln in open(COV,encoding='utf-8',errors='replace').read().split(chr(10))[1:]:
    p=ln.split(chr(9))
    if len(p)<8 or p[1].strip().upper()!='S13': continue
    if p[4].strip()!='[已证]': continue
    sites=idx.get(p[0].upper(),[])
    if sites: cnt+=1; print(p[0],p[2][:35],'n_sites',len(sites),sites[:2])
print('S13 [已证] rows with >=1 direct call site:',cnt)
