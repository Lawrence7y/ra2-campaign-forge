import hashlib,os,time,json,csv,collections,datetime
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE=os.path.join(ROOT,r"ra2youli\gamemd.exe")
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest().upper()
def rows(p):
 with open(p,'r',encoding='utf-8-sig',newline='') as f: return [r for r in csv.reader(f,delimiter='\t')]
cov=rows(COV); atl=rows(ATL)
if cov and cov[0][0]=='entry,subsystem': cov=cov[1:]
if atl and atl[0][0]=='entry': atl=atl[1:]
ats={r[0].lower():r for r in atl if r}
s10=[r for r in cov if len(r)>=8 and r[1]=='S10']
inter=[r for r in s10 if r[0].lower() in ats]
g=collections.Counter(r[4] for r in inter)
namedL=sum(1 for r in inter if r[2] and not r[2].startswith('sub_'))
namedS=sum(1 for r in inter if r[2] and not r[2].startswith('sub_') and '::sub_' not in r[2])
res={'time':datetime.datetime.now().astimezone().isoformat(),'exe_sha':sha(EXE),'cov_sha':sha(COV),'cov_size':os.path.getsize(COV),'cov_mtime':datetime.datetime.fromtimestamp(os.path.getmtime(COV)).astimezone().isoformat(),'atl_sha':sha(ATL),'s10_rows':len(s10),'intersection':len(inter),'outside':len(s10)-len(inter),'grades':dict(g),'proved':g['[已证]'],'named_L':namedL,'named_S':namedS,'proved_pct':g['[已证]']*100/len(inter),'named_L_pct':namedL*100/len(inter)}
text=json.dumps(res,ensure_ascii=False,indent=2)
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\EVIDENCE\BASELINE.txt",'w',encoding='utf-8') as f: f.write(text+'\n')
print(text)
