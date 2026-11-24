import sys,csv,hashlib,datetime,collections
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
L=[]
def log(s=''): L.append(str(s))
log('S10_K13 BASELINE (fresh read)')
log('TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
log('EXE='+str(R.EXE)+' size='+str(R.EXE.stat().st_size)+' sha='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper())
log('COV='+str(COV)+' size='+str(COV.stat().st_size)+' sha='+hashlib.sha256(COV.read_bytes()).hexdigest().upper()+' mtime='+datetime.datetime.fromtimestamp(COV.stat().st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat())
log('ATL='+str(ATL)+' size='+str(ATL.stat().st_size)+' sha='+hashlib.sha256(ATL.read_bytes()).hexdigest().upper())
with ATL.open(encoding='utf-8-sig',newline='') as f:
    atl={r['entry'].strip().lower() for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t'))
s10=[r for r in rows if r['subsystem'].strip().upper()=='S10']
inside=[r for r in s10 if r['entry'].strip().lower() in atl]
entries={r['entry'].strip().lower() for r in inside}
ctr=collections.Counter()
for r in inside: ctr[r['grade'].strip().upper()]+=1
proved=ctr['[已证]']
named_l=sum(1 for r in inside if r['name'].strip() and not r['name'].strip().lower().startswith('sub_'))
named_s=sum(1 for r in inside if r['name'].strip() and not r['name'].strip().lower().startswith('sub_') and '::sub_' not in r['name'].strip().lower())
log(f'COV_ROWS={len(rows)} S10_ROWS={len(s10)} S10_IN_ATLAS={len(inside)} S10_OUTSIDE={len(s10)-len(inside)}')
log('GRADE_5TH_COL='+repr(dict(ctr)))
log(f'PROVED={proved} PROVED_PCT={100*proved/len(inside):.4f} THRESHOLD={(len(inside)+1)//2} GAP={(len(inside)+1)//2-proved}')
log(f'NAMED_L={named_l} NAMED_L_PCT={100*named_l/len(inside):.4f} NAMED_S={named_s}')
with COV.open(encoding='utf-8',newline='') as f:
    rd=csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t'); hdr=rd.fieldnames
log('HEADER='+repr(hdr))
out=str(ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/BASELINE.txt')
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))
