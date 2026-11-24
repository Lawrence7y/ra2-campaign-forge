
from pathlib import Path
import csv,hashlib,datetime,re,collections
ROOT=Path(r'D:\Project\ra2-campaign-forge')
C=ROOT/'lead/next_re_20261117_r14/S10_K9'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
raw=(C/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines()
rows=[x.split('\t') for x in raw if x]
assert rows and all(len(x)==9 for x in rows),('COLS',[len(x) for x in rows])
assert len({x[0].upper() for x in rows})==len(rows),'DUP_ENTRY'
assert len({x[2] for x in rows})==len(rows),'DUP_NAME'
assert all(x[4]=='[已证]' for x in rows),'GRADE'
assert all(x[8] in {'symbolic','behavioral','placeholder'} for x in rows),'NAME_KIND'
assert all('+0x' not in x[2].lower() for x in rows),'OFFSET_IN_NAME'
base={r['entry'].strip().upper():r for r in csv.DictReader(COV.open(encoding='utf-8',newline=''),delimiter='\t')}
atl={r['entry'].strip().lower() for r in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t')}
for x in rows:
 assert x[1]=='S10',('SUB',x[0])
 b=base.get(x[0].upper());assert b,('NO_BASE',x[0])
 assert b['grade'].strip().upper()!='[已证]',('ALREADY_PROVED',x[0])
 assert x[0].lower() in atl,('NOT_ATLAS',x[0])
 pth,split=(x[5].split('#',1)+[''])[:2]
 f=C/pth;assert f.exists(),('NO_EVIDENCE',x[0],f)
 txt=f.read_text(encoding='utf-8')
 assert split in txt,('NO_ANCHOR',x[0],split)
 assert b['entry'].upper() in txt or x[0] in txt,('NO_ENTRY_EVIDENCE',x[0])
# grade-only baseline: raw fifth column of S10 entries in atlas
s10=[r for r in base.values() if r['subsystem'].strip().upper()=='S10' and r['entry'].strip().lower() in atl]
with COV.open(encoding='utf-8') as f:
 f.readline();cnt=collections.Counter()
 es={r['entry'].strip().lower() for r in s10}
 for line in f:
  z=line.rstrip('\n').split('\t')
  if z[0].strip().lower() in es:cnt[z[4].strip().upper()]+=1
proved=cnt['[已证]'];sim=proved+len(rows)
def namedL(n):return bool(n.strip()) and not n.strip().lower().startswith('sub_')
def namedS(n):return namedL(n) and not re.search(r'::sub_[0-9a-fA-F]{8}$',n.strip())
def strict(n):return namedS(n) and not re.search(r'::(?:v?slot)\d+$',n.strip())
base_nL=sum(namedL(r['name']) for r in s10);base_nS=sum(namedS(r['name']) for r in s10);base_st=sum(strict(r['name']) for r in s10)
sim_nL=base_nL+sum(namedL(x[2]) for x in rows);sim_nS=base_nS+sum(namedS(x[2]) for x in rows);sim_st=base_st+sum(strict(x[2]) for x in rows)
L=['S10_K9 DELTA VALIDATE','TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA256='+hashlib.sha256(EXE.read_bytes()).hexdigest().upper(),'DELTA_ROWS='+str(len(rows)),'COLS=9 ENTRY_UNIQUE=1 NAME_UNIQUE=1 GRADE_OK=1 EVIDENCE_ANCHORS_OK=1','NAME_KIND='+repr(dict(collections.Counter(x[8] for x in rows))),'BASE_PROVED='+str(proved),'SIM_PROVED='+str(sim),'SIM_PCT='+f'{100*sim/len(s10):.4f}','THRESHOLD=263 NEED='+str(max(0,263-sim)),'BASE_NAMED_L_CURRENT='+str(base_nL)+' SIM_NAMED_L='+str(sim_nL),'BASE_NAMED_S_CURRENT='+str(base_nS)+' SIM_NAMED_S='+str(sim_nS),'BASE_NAMED_STRICT='+str(base_st)+' SIM_NAMED_STRICT='+str(sim_st),'NOTE=card named_L=511 differs from current name-column recompute 513; not used for grade-only baseline.']
for x in rows:L.append('ROW '+x[0]+' base_grade='+base[x[0].upper()]['grade'].strip()+' name_kind='+x[8]+' conflict='+x[7])
(C/'EVIDENCE/DELTA_VALIDATE.txt').write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))
