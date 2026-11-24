import os,json,re,collections
ROOT=r'D:\Project\ra2-campaign-forge'
SEARCH=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\EVIDENCE'
entries=['0045A680','0045A730','0045AB50','0045AC30','004D24A0','004D2510','004D27D0','004D2810']
exts={'.md','.tsv','.json','.txt','.py','.js','.cjs','.mjs','.yml','.yaml'}
skip={'.git','node_modules','__pycache__','.asar-dump','.dsh-watch','.tmp'}
pats={}
for e in entries:
 six=e[2:]
 pats[e]=[re.compile(r'(?<![0-9A-Fa-f])'+e+r'(?![0-9A-Fa-f])'),re.compile(r'(?<![0-9A-Fa-f])'+six+r'(?![0-9A-Fa-f])')]
counts={e:[0,0] for e in entries}; files={e:set() for e in entries}
for dp,dn,fn in os.walk(SEARCH):
 dn[:]=[d for d in dn if d not in skip]
 for name in fn:
  if os.path.splitext(name)[1].lower() not in exts: continue
  p=os.path.join(dp,name)
  try:
   if os.path.getsize(p)>20*1024*1024: continue
  except: continue
  try: s=open(p,encoding='utf-8',errors='ignore').read()
  except: continue
  for e in entries:
   for idx,pat in enumerate(pats[e]):
    n=len(pat.findall(s))
    if n:
     counts[e][idx]+=n; files[e].add(p)
cov=[]
with open(os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv'),encoding='utf-8') as f:
 lines=f.read().splitlines()
for l in lines[1:]:
 parts=l.split('\t')
 if len(parts)>=5 and parts[0] in entries:
  cov.append({'entry':parts[0],'subsystem':parts[1],'name':parts[2],'grade':parts[4],'conflict':parts[7] if len(parts)>7 else ''})
conflicts=[]
with open(os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE','CONFLICTS.tsv'),encoding='utf-8') as f:
 for l in f.read().splitlines()[1:]:
  if any(e in l for e in entries): conflicts.append(l)
rows=[]
for e in entries:
 c=[x for x in cov if x['entry']==e]
 names=sorted(set(x['name'] for x in c)); subs=sorted(set(x['subsystem'] for x in c)); grades=sorted(set(x['grade'] for x in c))
 conflict_flag=(len(names)>1 or len(subs)>1 or len(grades)>1 or any(str(x.get('conflict'))=='1' for x in c) or any(e in l for l in conflicts))
 rows.append({'entry':e,'cov_rows':len(c),'names':names,'subsystems':subs,'grades':grades,'hits8':counts[e][0],'hits6':counts[e][1],'files':len(files[e]),'conflict':conflict_flag})
with open(os.path.join(OUT,'conflict18.tsv'),'w',encoding='utf-8') as f:
 f.write('entry\tcov_rows\tnames\tsubsystems\tgrades\thits8\thits6\tfiles\tconflict\n')
 for r in rows:
  f.write('\t'.join([r['entry'],str(r['cov_rows']),'|'.join(r['names']),'|'.join(r['subsystems']),'|'.join(r['grades']),str(r['hits8']),str(r['hits6']),str(r['files']),str(r['conflict']).lower()])+'\n')
json.dump(rows,open(os.path.join(OUT,'conflict18.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
for r in rows: print(r['entry'],'cov',r['cov_rows'],'8',r['hits8'],'6',r['hits6'],'conflict',r['conflict'])
