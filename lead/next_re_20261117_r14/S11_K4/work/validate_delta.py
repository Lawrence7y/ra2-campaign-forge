#!/usr/bin/env python3
"""Independent validator for S11_K4/coverage_delta.tsv.

Checks: no header, 6 columns, hex8 entry, S11, grade token, evidence paths exist,
entry is in fresh vtable evidence or proven closure/ctor, no shared stub claim,
and recomputes coverage∩atlas post-merge counts without writing coverage.tsv.
"""
from pathlib import Path
import csv,re,json,collections
ROOT=Path(r'D:\Project\ra2-campaign-forge'); R=ROOT/'lead/next_re_20261117_r14'; CARD=R/'S11_K4'
p=CARD/'coverage_delta.tsv'
lines=p.read_text(encoding='utf-8').splitlines()
bad=[]; rows=[]
for n,line in enumerate(lines,1):
    f=line.split('\t')
    if len(f)!=6: bad.append((n,'cols',len(f))); continue
    if not re.fullmatch(r'[0-9A-F]{8}',f[0]): bad.append((n,'entry',f[0]))
    if f[1]!='S11': bad.append((n,'subsystem',f[1]))
    if f[4]!='[已证]': bad.append((n,'grade',f[4]))
    for ep in f[5].split(';'):
        if not (CARD/ep).exists(): bad.append((n,'evidence',ep))
    rows.append(f)
ent=json.loads((CARD/'work/entry_evidence.json').read_text(encoding='utf-8'))
clo=json.loads((CARD/'work/closure.json').read_text(encoding='utf-8'))
allowed=set(ent)|{r['off0_slot9'] for r in clo}|{r['ctor'] for r in clo}
for f in rows:
    if f[0] not in allowed: bad.append(('row','not_allowed',f[0]))
    if f[0]=='004C9150': bad.append(('row','shared_stub',f[0]))
with (R/'COVERAGE/coverage.tsv').open(encoding='utf-8',newline='') as fh:
 cov=[r for r in csv.DictReader(fh,delimiter='\t') if r['subsystem']=='S11']
with (ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv').open(encoding='utf-8',newline='') as fh:
 atl={r['entry'].lower() for r in csv.DictReader(fh,delimiter='\t')}
delta={r[0] for r in rows}
inter={r['entry'].upper() for r in cov if r['entry'].lower() in atl}
before=sum(1 for r in cov if r['entry'].upper() in inter and r['grade'].strip()=='[已证]')
after=before+len(delta&inter)
named=[]
for r in cov:
    if r['entry'].upper() not in inter: continue
    nm=r['name'].strip()
    if nm and not nm.startswith('sub_') and '::sub_' not in nm: named.append(r['entry'].upper())
# renamed sub_ rows become named via delta; compute explicitly
renamed_named=sum(1 for f in rows if f[0] in inter and f[2].strip() and not f[2].startswith('sub_') and '::sub_' not in f[2] and any(r['entry'].upper()==f[0] and (r['name'].strip().startswith('sub_') or '::sub_' in r['name']) for r in cov))
rep=[]
rep.append('ROWS=%d UNIQUE=%d BAD=%d'%(len(rows),len(delta),len(bad)))
for b in bad[:50]: rep.append('BAD '+repr(b))
rep.append('BEFORE_ATLAS_PROVED=%d AFTER_ATLAS_PROVED=%d DEN=%d PCT=%.4f'%(before,after,len(inter),100*after/len(inter)))
rep.append('NAMED_S_BEFORE=%d NAMED_S_AFTER_UPPERBOUND=%d'%(len(named),len(named)+renamed_named))
rep.append('SHARED_STUB_CLAIMS=%d'%sum(1 for f in rows if f[0]=='004C9150'))
(CARD/'work/validate_delta.log').write_text('\n'.join(rep)+'\n',encoding='utf-8')
print('\n'.join(rep))
