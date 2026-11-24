
import csv,hashlib
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
targets=['0065CAC0','004324B0','00552490','006C9890','00631CC0','0065D150','00431E80']
print('sha',hashlib.sha256(open(p,'rb').read()).hexdigest().upper()[:16])
n=0;cnt={}
with open(p,encoding='utf-8',errors='replace') as f:
    lines=f.read().split('\n')
print('wc lines',len(lines))
hdr=lines[0]; print('HEADER',hdr[:200])
for line in lines[1:]:
    if not line.strip():continue
    n+=1
    fs=line.split('\t')
    if len(fs)<5: continue
    if fs[1]=='S03': cnt[fs[4]]=cnt.get(fs[4],0)+1
    if fs[0].upper() in targets:
        print('ROW',fs[0],'|sub=',fs[1],'|name=',fs[2],'|sem=',fs[3],'|grade=',fs[4])
print('data rows',n,'S03 grade dist',cnt)
