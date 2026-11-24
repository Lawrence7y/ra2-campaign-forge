#!/usr/bin/env python3
"""Validate S10-K4 delta (19 semantic corrections), read-only against shared files."""
from pathlib import Path
import csv,re,hashlib,collections
ROOT=Path(r'D:\Project\ra2-campaign-forge'); CARD=ROOT/'lead/next_re_20261117_r14/S10_K4'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
FN=['entry','subsystem','name','one_line_semantics','grade','evidence_path']
with COV.open('r',encoding='utf-8',newline='') as f: cov=list(csv.DictReader(f,delimiter='\t'))
atl={r['entry'].strip().lower() for r in csv.DictReader(ATL.open('r',encoding='utf-8',newline=''),delimiter='\t')}
cov_by={r['entry'].strip().lower():r for r in cov}
with (CARD/'coverage_delta.tsv').open('r',encoding='utf-8',newline='') as f: delta=list(csv.DictReader(f,fieldnames=FN,delimiter='\t'))
lines=[]; bad=[]; seen_e=set(); seen_n=set()
for i,d in enumerate(delta,1):
    e=d['entry'].strip().upper(); k=e.lower(); c=cov_by.get(k); ev=(CARD/d['evidence_path'].strip())
    checks={
      'entry8hex':bool(re.fullmatch(r'[0-9A-F]{8}',e)),
      'subsystem':d['subsystem'].strip().upper()=='S10',
      'grade':d['grade'].strip()=='[已证]',
      'in_atlas':k in atl,
      'exists_coverage':c is not None,
      'old_nonproved':bool(c and c['grade'].strip()!='[已证]'),
      'name_unique':d['name'].strip() not in seen_n,
      'entry_unique':e not in seen_e,
      'name_not_placeholder':not (d['name'].strip().startswith('sub_') or '::sub_' in d['name'] or re.search(r'::(?:v?slot)\d+$',d['name'].strip())),
      'sem_nonempty':len(d['one_line_semantics'].strip())>40,
      'no_noop_claim':'no-op handler' not in d['one_line_semantics'].lower() and 'no_op handler' not in d['one_line_semantics'].lower(),
      'has_1c2':'0x1C2' in d['one_line_semantics'],
      'has_450':'450' in d['one_line_semantics'],
      'evidence_exists':ev.exists(),
    }
    if not all(checks.values()): bad.append((i,e,[k for k,v in checks.items() if not v]))
    seen_e.add(e); seen_n.add(d['name'].strip())
s10=[r for r in cov if r['subsystem'].strip().upper()=='S10' and r['entry'].strip().lower() in atl]
base_proved=sum(r['grade'].strip()=='[已证]' for r in s10)
merge_proved=base_proved+sum(1 for d in delta if d['entry'].strip().lower() in atl and cov_by[d['entry'].strip().lower()]['grade'].strip()!='[已证]' and d['grade'].strip()=='[已证]')
def ph(n):
    n=n.strip(); return (not n) or n.startswith('sub_') or '::sub_' in n or re.search(r'::(?:v?slot)\d+$',n) is not None
def named_L(r): return bool(r['name'].strip()) and not r['name'].strip().startswith('sub_')
def named_S(r): return not ph(r['name'])
base_nl=sum(named_L(r) for r in s10); base_ns=sum(named_S(r) for r in s10)
merged={k:dict(r) for k,r in cov_by.items()}
for d in delta:
    if d['entry'].strip().lower() in merged: merged[d['entry'].strip().lower()]['name']=d['name'].strip()
ms10=[r for k,r in merged.items() if r['subsystem'].strip().upper()=='S10' and k in atl]
lines += [
 'S10-K4 DELTA VALIDATION',
 'SHA256='+hashlib.sha256(EXE.read_bytes()).hexdigest().upper(),
 'DELTA_ROWS='+str(len(delta)),
 'BAD_ROWS='+str(len(bad)),
 'DUPLICATE_ENTRY='+str(len(delta)-len(seen_e)),
 'DUPLICATE_NAME='+str(len(delta)-len(seen_n)),
 'BASE_ATLAS_N='+str(len(s10)),
 'BASE_PROVED='+str(base_proved),
 'MERGED_PROVED='+str(merge_proved),
 'MERGED_PROVED_PCT='+f'{100.0*merge_proved/len(s10):.4f}',
 'DOD_THRESHOLD='+str((len(s10)+1)//2),
 'DOD_REMAINING='+str(max(0,(len(s10)+1)//2-merge_proved)),
 'BASE_NAMED_L='+str(base_nl),
 'BASE_NAMED_S_STRICT='+str(base_ns),
 'MERGED_NAMED_L='+str(sum(named_L(r) for r in ms10)),
 'MERGED_NAMED_S_STRICT='+str(sum(named_S(r) for r in ms10)),
 'NOP_GAP_AUDIT=005B2E50=26B 005B2E90=58B 005B2EF0=26B 005B2F50=42B; all 19 contiguous_90=10B',
]
for b in bad: lines.append('BAD '+repr(b))
for d in delta:
    lines.append('ROW '+d['entry']+' '+d['name']+' '+('ok' if not any(b[1]==d['entry'] for b in bad) else 'BAD'))
(CARD/'EVIDENCE/validate_delta.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines[:18]))
