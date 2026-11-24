
from pathlib import Path
import csv,hashlib,datetime,collections
R=Path(r'D:\Project\ra2-campaign-forge')
COV=R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=R/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=R/'ra2youli/gamemd.exe'
OUT=R/'lead/next_re_20261117_r14/S10_K9/EVIDENCE/BASELINE_K9.txt'
def stamps(p):
 s=p.stat();return f'{datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()} size={s.st_size} sha256={hashlib.sha256(p.read_bytes()).hexdigest().upper()}'
with COV.open(encoding='utf-8',newline='') as f:
 rd=csv.DictReader(f,delimiter='\t');hdr=rd.fieldnames;cov=list(rd)
with ATL.open(encoding='utf-8',newline='') as f:
 atl={r['entry'].strip().lower() for r in csv.DictReader(f,delimiter='\t')}
s10=[r for r in cov if r.get('subsystem','').strip().upper()=='S10']
inside=[r for r in s10 if r['entry'].strip().lower() in atl]
# grade only from raw fifth column; case-normalized
entries={r['entry'].strip().lower() for r in inside}
with COV.open(encoding='utf-8') as f:
 f.readline();ctr=collections.Counter()
 for line in f:
  z=line.rstrip('\n').split('\t')
  if z[0].strip().lower() in entries: ctr[z[4].strip().upper()]+=1
proved=ctr['[已证]']
pct=100.0*proved/len(inside)
th=(len(inside)+1)//2
L=['S10_K9 BASELINE RECOMPUTE','READ_TIME_ISO='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'TOOLS=Python3.12.10 csv/hashlib; grade read ONLY from raw 5th column; entries case-normalized lower','COVERAGE='+str(COV),'COVERAGE_'+stamps(COV),'ATLAS='+str(ATL),'ATLAS_'+stamps(ATL),'EXE='+str(EXE),'EXE_'+stamps(EXE),'S10_ROWS='+str(len(s10)),'S10_IN_ATLAS='+str(len(inside)),'S10_OUTSIDE_ATLAS='+str(len(s10)-len(inside)),'GRADE_5TH_COL='+repr(dict(ctr)),'PROVED='+str(proved),'PROVED_PCT='+f'{pct:.4f}','THRESHOLD='+str(th),'NEED='+str(max(0,th-proved)),'CARD_PROVED=107/526 MATCH='+str(proved==107 and len(inside)==526),'NOTE=named_L not recomputed here because the card requires grade-only column-5 baseline; card value 511 is not used for grading.']
OUT.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L));assert (len(inside),proved)==(526,107)
