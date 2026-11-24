import os,csv,json,hashlib,time,collections
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE=os.path.join(ROOT,r"ra2youli\gamemd.exe")
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest().upper()
def rows(p):
 with open(p,'r',encoding='utf-8-sig',newline='') as f:return [r for r in csv.reader(f,delimiter='\t')]
cov=rows(COV);atl=rows(ATL)
if cov and cov[0][0]=='entry,subsystem':cov=cov[1:]
ats={r[0].lower():r for r in atl if r and r[0]}
s10=[r for r in cov if len(r)>=8 and r[1]=='S10']
inter=[r for r in s10 if r[0].lower() in ats];out=[r for r in s10 if r[0].lower() not in ats]
g=collections.Counter(r[4] for r in inter)
namedL=sum(1 for r in inter if r[2] and not r[2].lower().startswith('sub_'))
res={'time':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'exe_sha':sha(EXE),'exe_size':os.path.getsize(EXE),'cov_sha':sha(COV),'cov_size':os.path.getsize(COV),'cov_mtime':time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.path.getmtime(COV))),'atl_sha':sha(ATL),'s10_rows':len(s10),'intersection':len(inter),'outside':len(out),'grades':dict(g),'proved':g['[已证]'],'proved_pct':100*g['[已证]']/len(inter),'named_L':namedL,'named_pct':100*namedL/len(inter),'card_gate':263,'gap':263-g['[已证]']}
print(json.dumps(res,ensure_ascii=False,indent=2))
