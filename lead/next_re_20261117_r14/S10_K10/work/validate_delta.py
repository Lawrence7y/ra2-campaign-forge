from pathlib import Path
import csv,hashlib,datetime
R=Path(r'D:\Project\ra2-campaign-forge')
B=R/'lead/next_re_20261117_r14/S10_K10'
D=B/'coverage_delta.tsv'
rows=list(csv.reader(D.open(encoding='utf-8'),delimiter='\t'))
assert len(rows)==2 and all(len(r)==9 for r in rows), (len(rows),[len(r) for r in rows])
entries=[r[0] for r in rows]; names=[r[2] for r in rows]
assert len(set(entries))==2 and len(set(names))==2
assert all(r[1]=='S10' and r[4]=='[已证]' and r[7]=='0' and r[8]=='behavioral' for r in rows)
assert all('+0x' not in r[2] and not r[2].startswith('sub_') for r in rows)
assert all(any(k in r[2].lower() for k in ['behavior']) for r in rows)
for r in rows:
 ep=B/r[5].split('#')[0]
 assert ep.exists(), ep
 assert r[0] in ep.read_text('utf-8'), (r[0],ep)
cov={x['entry'].upper():x for x in csv.DictReader((R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv').open(encoding='utf-8'),delimiter='\t')}
for e in entries:
 assert cov[e]['subsystem']=='S10'
 assert cov[e]['grade']!='[已证]'
prev={'0051D6F0','0051DAF0','0051B1F0','0051BAB0','00522340'}
assert not (set(entries)&prev)
for f in ['PROGRESS.md','UNKNOWNS.md','DISAGREE.md','EVIDENCE/BASELINE_K10.txt','EVIDENCE/BASELINE_DISCREPANCY.txt','EVIDENCE/PROOF_R14.txt','EVIDENCE/CANDIDATE_SCAN.tsv','EVIDENCE/DIRECT_CALLERS_SCAN.tsv']:
 assert (B/f).exists(), f
L=['DELTA VALIDATE S10-K10', 'READ_TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(), 'DELTA='+str(D), 'DELTA_SHA256='+hashlib.sha256(D.read_bytes()).hexdigest().upper(), 'ROWS='+str(len(rows)), 'COLS='+','.join(str(len(r)) for r in rows), 'NAME_KIND='+','.join(r[8] for r in rows), 'N_SOURCES='+','.join(r[6] for r in rows), 'CONFLICT='+','.join(r[7] for r in rows), 'ENTRIES='+','.join(entries), 'PLACEHOLDER=0', 'K9_DUPLICATES=0', 'EVIDENCE_ANCHORS=OK', 'RESULT=PASS']
(B/'EVIDENCE/DELTA_VALIDATE_R14.txt').write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))
