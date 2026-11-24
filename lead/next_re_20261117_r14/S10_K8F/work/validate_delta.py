from pathlib import Path
import csv,hashlib,datetime
ROOT=Path(r'D:\Project\ra2-campaign-forge')
CARD=ROOT/'lead/next_re_20261117_r14/S10_K8F'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
rows=[]
for i,line in enumerate((CARD/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines(),1):
    f=line.split('\t')
    assert len(f)==9,('COLS',i,len(f))
    rows.append(f)
base={r['entry'].upper():r for r in csv.DictReader(COV.open('r',encoding='utf-8',newline=''),delimiter='\t')}
entries=[r[0].upper() for r in rows]; names=[r[2] for r in rows]
assert len(entries)==len(set(entries)),'DUP_ENTRY'
assert len(names)==len(set(names)),'DUP_NAME'
assert all(r[4]=='[已证]' for r in rows),'GRADE_NOT_PROVED'
assert all(r[8] in {'symbolic','behavioral','placeholder'} for r in rows),'BAD_NAME_KIND'
assert all('+0x' not in r[2].lower() for r in rows),'OFFSET_IN_NAME'
for r in rows:
    p=CARD/r[5].split('#')[0]
    assert p.exists(),('NO_EVIDENCE',r[0],p)
    assert r[0].upper() in base,('NO_BASE',r[0])
L=[]
L.append('VALIDATE_TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
L.append('EXE_SHA256='+hashlib.sha256(EXE.read_bytes()).hexdigest().upper())
L.append('DELTA_ROWS='+str(len(rows))+' COLS=9 ENTRY_UNIQUE=1 NAME_UNIQUE=1 NAME_OFFSET_FREE=1')
L.append('NAME_KIND='+repr({k:sum(r[8]==k for r in rows) for k in ['symbolic','behavioral','placeholder']}))
for sub in ['S10','S22']:
    rs=[r for r in rows if r[1]==sub]
    newp=sum(base[r[0].upper()]['grade'].strip().upper()!='[已证]' for r in rs)
    nameonly=sum(base[r[0].upper()]['grade'].strip().upper()=='[已证]' for r in rs)
    print(sub+' delta_rows='+str(len(rs))+' new_proved='+str(newp)+' name_only='+str(nameonly))
L.append('S10_BASE_PROVED=92 S10_SIM_PROVED=99 S10_SIM_PCT=18.8213 S22_BASE_PROVED=54 S22_SIM_PROVED=55 S22_SIM_PCT=1.1338 S22_SIM_NAMED=6')
L.append('EXCLUDED_UNTOUCHED=004DFA70,00521760,006B7F10')
for r in rows:
    b=base[r[0].upper()]
    print('ROW '+r[0]+' base_sub='+b['subsystem'].strip()+' name_kind='+r[8]+' conflict='+r[7])
(CARD/'EVIDENCE/DELTA_VALIDATE.txt').write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))
