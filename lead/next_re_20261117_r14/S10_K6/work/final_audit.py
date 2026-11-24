#!/usr/bin/env python3
"""Final artifact audit for S10-K6."""
from pathlib import Path
import csv,re,hashlib,datetime
card=Path(__file__).resolve().parent.parent
root=Path(r'D:\Project\ra2-campaign-forge')
EXE=root/'ra2youli/gamemd.exe'; COV=root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper(); st=COV.stat()
L=[]
L.append('EXE_SHA256='+sha+' MATCH='+str(sha=='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'))
L.append('COVERAGE_MTIME='+datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()+' SIZE='+str(st.st_size))
for r in ['PROGRESS.md','UNKNOWNS.md','DISAGREE.md','coverage_delta.tsv','EVIDENCE','work']:
 L.append('REQUIRED '+r+' EXISTS='+str((card/r).exists()))
prog=(card/'PROGRESS.md').read_text(encoding='utf-8').splitlines()
L.append('PROGRESS_LINES='+str(len(prog))+' LE60='+str(len(prog)<=60))
F=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
lines=(card/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines()
rows=[dict(zip(F,x)) for x in csv.reader(lines,delimiter='\t')]
L.append('DELTA_LINES='+str(len(lines))+' NO_HEADER='+str(not lines[0].startswith('entry\t')))
E={'005B3A60','005B3970','004E0170','00523350','006B1390','006B8140','00746E80'}
ok=True
for r in rows:
 ev=card/r['evidence_path'].split('#')[0]
 p=ev.is_file(); hit=p and r['entry'] in ev.read_text(encoding='utf-8',errors='replace')
 ok=ok and p and hit and r['grade'].strip()=='[已证]' and r['entry'].upper() not in E
 L.append('EVID '+r['entry']+' '+r['name']+' EXISTS='+str(p)+' ENTRY_IN_FILE='+str(hit)+' BYTES='+str(ev.stat().st_size if p else 0))
names=[r['name'] for r in rows]; entries=[r['entry'].upper() for r in rows]
L.append('ALL_EVIDENCE_OK='+str(ok))
L.append('DUP_ENTRY='+str(len(entries)-len(set(entries)))+' DUP_NAME='+str(len(names)-len(set(names))))
L.append('FORBIDDEN_TOUCHED='+str(bool(set(entries)&E)))
L.append('PLACEHOLDER_NAME='+str(sum(bool(re.search(r'::(?:v?slot)\d+$',n) or n.startswith('sub_') or '::sub_' in n) for n in names)))
for f in sorted((card/'EVIDENCE').iterdir()): L.append('EVIDENCE_FILE '+f.name+' '+str(f.stat().st_size))
L.append('WORK_SCRIPTS='+str(len(list((card/'work').glob('*.py')))))
(card/'EVIDENCE/final_audit.txt').write_text('\n'.join(L)+'\n',encoding='utf-8')
print('\n'.join(L))
if not ok or len(entries)!=len(set(entries)) or len(names)!=len(set(names)) or set(entries)&E: raise SystemExit(2)
