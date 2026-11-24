import os, hashlib, datetime
root=r'D:/Project/ra2-campaign-forge'
cov=root+'/lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
exe=root+'/ra2youli/gamemd.exe'
tz=datetime.timezone(datetime.timedelta(hours=8))
print('SAMPLE',datetime.datetime.now(tz).isoformat())
for x in [cov,exe]:
 b=open(x,'rb').read(); st=os.stat(x)
 print('FILE',x,'size',len(b),'sha256',hashlib.sha256(b).hexdigest().upper(),'mtime',datetime.datetime.fromtimestamp(st.st_mtime,tz).isoformat())
lines=open(cov,'r',encoding='utf-8',errors='replace').read().splitlines()
rows=[l.split('\t') for l in lines[1:] if l.strip()]
s10=[r for r in rows if len(r)>=5 and r[1].upper()=='S10']
print('HEADER',lines[0])
print('S10',len(s10),'PROVED5',sum(1 for r in s10 if r[4].strip().upper()=='[已证]'))
allpr=sum(1 for r in rows if len(r)>=5 and r[4].strip().upper()=='[已证]')
print('ALL',len(rows),'PROVED5_ALL',allpr)
