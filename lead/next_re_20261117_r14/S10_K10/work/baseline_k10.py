from pathlib import Path
import csv,hashlib,datetime,collections
R=Path(r'D:\Project\ra2-campaign-forge')
COV=R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=R/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=R/'ra2youli/gamemd.exe'
OUT=R/'lead/next_re_20261117_r14/S10_K10/EVIDENCE/BASELINE_K10.txt'
def stamps(p):
 s=p.stat();return f'{datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()} size={s.st_size} sha256={hashlib.sha256(p.read_bytes()).hexdigest().upper()}'
with COV.open(encoding='utf-8',newline='') as f:
 cov=list(csv.DictReader(f,delimiter='\t'))
with ATL.open(encoding='utf-8',newline='') as f:
 atl={r['entry'].strip().lower() for r in csv.DictReader(f,delimiter='\t')}
s10=[r for r in cov if r.get('subsystem','').strip().upper()=='S10']
inside=[r for r in s10 if r['entry'].strip().lower() in atl]
entries={r['entry'].strip().lower() for r in inside}
with COV.open(encoding='utf-8') as f:
 f.readline();ctr=collections.Counter()
 for line in f:
  z=line.rstrip('\n').split('\t')
  if z[0].strip().lower() in entries: ctr[z[4].strip().upper()]+=1
proved=ctr['[已证]'];pct=100.0*proved/len(inside);th=(len(inside)+1)//2
L=['S10_K10 BASELINE RECOMPUTE','READ_TIME_ISO='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'GRADE_SOURCE=raw 5th column only; entries case-normalized lower','COVERAGE='+str(COV),'COVERAGE_'+stamps(COV),'ATLAS='+str(ATL),'ATLAS_'+stamps(ATL),'EXE='+str(EXE),'EXE_'+stamps(EXE),'S10_ROWS='+str(len(s10)),'S10_IN_ATLAS='+str(len(inside)),'S10_OUTSIDE_ATLAS='+str(len(s10)-len(inside)),'GRADE_5TH_COL='+repr(dict(ctr)),'PROVED='+str(proved),'PROVED_PCT='+f'{pct:.4f}','THRESHOLD='+str(th),'NEED='+str(max(0,th-proved)),'CARD_PROVED=112/526 MATCH='+str(proved==112 and len(inside)==526)]
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L));assert (len(inside),proved)==(526,112)
