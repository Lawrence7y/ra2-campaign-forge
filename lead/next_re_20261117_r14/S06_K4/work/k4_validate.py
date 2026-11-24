#!/usr/bin/env python3
"""S06-K4 baseline recomputation and delta validation. Read-only for shared files."""
from pathlib import Path
import csv,collections,hashlib,re
ROOT=Path(r"D:\Project\ra2-campaign-forge")
EXE=ROOT/"ra2youli/gamemd.exe"; COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"; ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
CARD=ROOT/"lead/next_re_20261117_r14/S06_K4"
def rows(p):
 with p.open('r',encoding='utf-8',newline='') as f: return list(csv.DictReader(f,delimiter='\t'))
def norm(x): return x.strip().lower()
cov=[r for r in rows(COV) if r.get('subsystem','').strip().upper()=='S06']
cov_by={norm(r['entry']):r for r in cov}
atl={norm(r['entry']) for r in rows(ATL)}
inter=sorted(set(cov_by)&atl)
grades=collections.Counter(cov_by[e]['grade'].strip() for e in inter)
namedL=sum(1 for e in inter if cov_by[e]['name'].strip() and not cov_by[e]['name'].strip().startswith('sub_'))
namedS=sum(1 for e in inter if cov_by[e]['name'].strip() and not cov_by[e]['name'].strip().startswith('sub_') and not re.search(r'::sub_[0-9A-Fa-f]{8}$',cov_by[e]['name'].strip()))
old_proved=grades['[已证]']
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
b=[]
b.append("S06-K4 BASELINE RECOMPUTE (on-disk truth; case-normalized entry sets)")
b.append("SHA256="+sha)
b.append("S06_ROWS=%d ATLAS_INTERSECTION=%d GRADES=%r"%(len(cov),len(inter),dict(grades)))
b.append("NAMED_L=%d NAMED_S_no_sub8=%d OLD_PROVED=%d PCT=%.4f%%"%(namedL,namedS,old_proved,100.0*old_proved/len(inter)))
b.append("DOD_PROVED_THRESHOLD_50PCT=%d (ceil(0.5*%d))"%((len(inter)+1)//2,len(inter)))
(CARD/'EVIDENCE/baseline_recompute.txt').write_text("\n".join(b)+"\n",encoding='utf-8')
delta=[]
with (CARD/'coverage_delta.tsv').open('r',encoding='utf-8',newline='') as f:
    for line in f:
        c=line.rstrip('\r\n').split('\t')
        if len(c)>=6: delta.append(dict(zip(['entry','subsystem','name','one_line_semantics','grade','evidence_path'],c[:6])))
bad=[]; gains=[]; oldg=collections.Counter(); names=collections.Counter()
for r in delta:
 e=norm(r['entry']); names[r['name'].strip()]+=1; old=r['entry'].strip().upper()
 if e not in cov_by: bad.append(('not_in_coverage',old)); continue
 o=cov_by[e]
 if o.get('subsystem','').strip().upper()!='S06': bad.append(('subsystem',old))
 if r.get('subsystem','').strip().upper()!='S06': bad.append(('delta_subsystem',old))
 if r.get('grade','').strip()!='[已证]': bad.append(('grade_not_proved',old))
 if o.get('grade','').strip()=='[已证]': bad.append(('already_proved',old))
 oldg[o.get('grade','').strip()]+=1
 if re.search(r'::slot\d+$',r['name'].strip()) or re.search(r'::sub_[0-9A-Fa-f]{8}$',r['name'].strip()): bad.append(('placeholder_name',old))
 if not r.get('one_line_semantics','').strip(): bad.append(('no_semantics',old))
 ev=CARD/r.get('evidence_path','')
 if not ev.exists() or ev.stat().st_size<10: bad.append(('evidence_missing',old))
 gains.append(old)
dupe_entries=[e for e,c in collections.Counter(norm(r['entry']) for r in delta).items() if c>1]
dupe_names=[n for n,c in names.items() if c>1]
new_proved=old_proved+len(gains)
v=[]
v.append("S06-K4 DELTA VALIDATION")
v.append("SHA256="+sha)
v.append("BASELINE_ROWS=%d INTER=%d OLD_PROVED=%d"%(len(cov),len(inter),old_proved))
v.append("DELTA_ROWS=%d OLD_GRADE_MIX=%r NEW_PROVED=%d NEW_PCT=%.4f%%"%(len(delta),dict(oldg),new_proved,100.0*new_proved/len(inter)))
v.append("DUPLICATE_ENTRIES=%d DUPLICATE_NAMES=%d BAD=%d"%(len(dupe_entries),len(dupe_names),len(bad)))
v.append("PLACEHOLDER_NAMES=0 (enforced: no ::slotN, no ::sub_XXXXXXXX)")
for x in bad: v.append("BAD "+repr(x))
for x in dupe_entries: v.append("DUPE_ENTRY "+x)
for x in dupe_names: v.append("DUPE_NAME "+x)
if bad or dupe_entries or dupe_names: raise SystemExit('\n'.join(v))
(CARD/'EVIDENCE/validate_delta.txt').write_text("\n".join(v)+"\n",encoding='utf-8')
print("\n".join(v))
