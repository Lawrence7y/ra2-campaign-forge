import sys,io,collections,hashlib
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
print('sha',hashlib.sha256(open(p,'rb').read()).hexdigest())
rows=[x for x in open(p,encoding='utf-8').read().splitlines()[1:] if x.strip()]
s20=[x for x in rows if x.split('\t')[1]=='S20']
print('S20 rows',len(s20),'grades',dict(collections.Counter(x.split('\t')[4] for x in s20)))
for a in ['004C54E0','0062DF20','0062E070','0062F230','0070F1D0','0070FD70','00739AC0','00739CD0','0075E950','007610F0','007C978A']:
    r=[x for x in s20 if x.split('\t')[0]==a]
    print(a, r[0].split('\t')[4] if r else 'MISSING')
