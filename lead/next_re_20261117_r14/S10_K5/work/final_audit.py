#!/usr/bin/env python3
"""Final artifact audit for S10-K5."""
from pathlib import Path
import csv,hashlib,datetime
CARD=Path(__file__).resolve().parent.parent
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
lines=[]
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
lines.append('SHA256='+sha+' MATCH='+str(sha=='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'))
st=COV.stat()
lines.append('COVERAGE_MTIME='+datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()+' SIZE='+str(st.st_size))
req=['PROGRESS.md','UNKNOWNS.md','DISAGREE.md','coverage_delta.tsv','EVIDENCE','work']
for r in req: lines.append('REQUIRED '+r+' EXISTS='+str((CARD/r).exists()))
prog=(CARD/'PROGRESS.md').read_text(encoding='utf-8').splitlines()
lines.append('PROGRESS_LINES='+str(len(prog))+' LE60='+str(len(prog)<=60))
delta=(CARD/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines()
lines.append('DELTA_LINES='+str(len(delta)))
lines.append('DELTA_HEADER_ABSENT='+str(not delta[0].startswith('entry\t')))
FIELDS=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
rows=[dict(zip(FIELDS,row)) for row in csv.reader((CARD/'coverage_delta.tsv').open('r',encoding='utf-8',newline=''),delimiter='\t')]
lines.append('DELTA_ROWS='+str(len(rows)))
ok=True
for r in rows:
 ev=CARD/r['evidence_path'].split('#')[0]
 hit=ev.is_file() and (r['entry'] in ev.read_text(encoding='utf-8',errors='replace'))
 ok=ok and hit
 lines.append('EVID '+r['entry']+' '+r['grade']+' '+r['name']+' EXISTS='+str(ev.is_file())+' ENTRY_IN_FILE='+str(hit)+' BYTES='+str(ev.stat().st_size if ev.is_file() else 0))
lines.append('ALL_EVIDENCE_OK='+str(ok))
for f in sorted((CARD/'EVIDENCE').iterdir()): lines.append('EVIDENCE_FILE '+f.name+' '+str(f.stat().st_size))
lines.append('WORK_SCRIPTS='+str(len(list((CARD/'work').glob('*.py')))))
(CARD/'EVIDENCE'/'final_audit.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
