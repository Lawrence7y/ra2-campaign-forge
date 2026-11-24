import os,json,hashlib,datetime
root=r'D:/Project/ra2-campaign-forge'
cov=root+'/lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
exe=root+'/ra2youli/gamemd.exe'
print('SAMPLE',datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
for p in [cov,exe]:
 b=open(p,'rb').read(); st=os.stat(p)
 print('FILE',p,'size',len(b),'sha256',hashlib.sha256(b).hexdigest().upper(),'mtime',datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat())
lines=open(cov,'r',encoding='utf-8',errors='replace').read().splitlines()
hdr=lines[0].split('\t'); print('HDR',hdr)
rows=[l.split('\t') for l in lines[1:] if l.strip()]
s10=[r for r in rows if r[1].upper()=='S10']
en=set()
for line in open(root+'/re_atlas/atlas.tsv','r',encoding='utf-8',errors='replace'):
 p=line.rstrip('\n').split('\t');
 if p and p[0].upper().startswith('0X'): en.add(int(p[0],16))
elif False else None
