from pathlib import Path
import csv,collections,hashlib,re,datetime
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
def rows(p):
 with p.open('r',encoding='utf-8',newline='') as f: yield from csv.DictReader(f,delimiter='\t')
def norm(x):return x.strip().lower()
def named_s(r):
 n=r.get('name','').strip();return bool(n) and not n.startswith('sub_') and '::sub_' not in n and re.search(r'::(?:v?slot)\d+$',n) is None
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
cov=[r for r in rows(COV) if r.get('subsystem','').strip().upper()=='S10']
atl={norm(r['entry']) for r in rows(ATL)};by={norm(r['entry']):r for r in cov}
inter=sorted(set(by)&atl);outside=sorted(set(by)-atl);ci=[by[e] for e in inter]
proved=sum(r['grade'].strip().upper()=='[已证]' for r in ci)
print('READ_TIME_ISO='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
print('EXE_SHA256='+sha)
st=COV.stat();print('COVERAGE_MTIME_ISO='+datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'SIZE='+str(st.st_size))
print('ATLAS_ROWS='+str(len(atl)),'S10_ROWS='+str(len(cov)),'INTER='+str(len(inter)),'OUTSIDE='+str(len(outside)))
print('GRADES='+repr(dict(collections.Counter(r['grade'].strip() for r in ci))))
print('PROVED='+str(proved),'PCT='+f'{100.0*proved/len(inter):.4f}','NAMED_S='+str(sum(named_s(r) for r in ci)))
th=(len(inter)+1)//2;print('THRESHOLD='+str(th),'NEED='+str(max(0,th-proved)))
for a in ['004DF320','004DF3A0','004DFA70','00521760','006F4960','004DFB70','004DFCB0','004DFE00','004E0E80','006B6EA0','006B6FA0','006B6C90','006B7F10']:
 r=by.get(a.lower());print('ROW',a,'grade='+(r['grade'].strip() if r else 'NONE'),'name='+(r['name'].strip() if r else 'NONE'))
