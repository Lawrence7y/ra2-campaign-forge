from __future__ import annotations
import hashlib, os, re
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=r'D:\Project\ra2-campaign-forge'
COV=ROOT+r'\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL=ROOT+r'\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EXE=ROOT+r'\ra2youli\gamemd.exe'
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def norm(a): return a.strip().lower()
def is_named(name:str)->bool:
    n=(name or '').strip()
    if not n or n.startswith('sub_'): return False
    if re.search(r'::sub_[0-9A-Fa-f]{6,8}$', n): return False
    return True
def load_rows(path, sep, header_sep=None):
    with open(path,'r',encoding='utf-8-sig',newline='') as f:
        raw=f.read().splitlines()
    header=raw[0].split(header_sep or sep)
    rows=[]
    for ln in raw[1:]:
        if not ln.strip(): continue
        part=ln.split(sep)
        if len(part)<len(header): part += ['']*(len(header)-len(part))
        rows.append(dict(zip(header,part)))
    return rows
cov_rows=load_rows(COV,'\t',',')
atl_rows=load_rows(ATL,'\t')
cov={norm(r['entry']):r for r in cov_rows if r.get('entry')}
atl={norm(r['entry']):r for r in atl_rows if r.get('entry')}
s17={a:r for a,r in cov.items() if r.get('subsystem','').strip().upper()=='S17'}
inter={a:r for a,r in s17.items() if a in atl}
outside=sorted(set(s17)-set(inter))
names=sorted(a for a,r in inter.items() if is_named(r.get('name','')))
named_L=sorted(a for a,r in inter.items() if (r.get('name','').strip() and not r.get('name','').strip().startswith('sub_')))
proved=sorted(a for a,r in inter.items() if r.get('grade','').strip()=='[已证]')
unnamed=sorted(a for a,r in inter.items() if not is_named(r.get('name','')))
h=hashlib.sha256()
with open(EXE,'rb') as f:
    for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
lines=[]
lines.append('S17_K5 baseline recomputation')
lines.append('time_asia_shanghai='+datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'))
lines.append('exe_sha256='+h.hexdigest().upper())
lines.append('coverage_data_rows='+str(len(cov_rows))+' atlas_data_rows='+str(len(atl_rows)))
lines.append('S17_coverage_rows='+str(len(s17))+' S17_inter_atlas='+str(len(inter))+' S17_outside_atlas='+str(len(outside)))
lines.append('named_L='+str(len(named_L))+' named_S='+str(len(names))+' pct='+f'{100*len(names)/len(inter):.2f}%')
lines.append('proved_col5='+str(len(proved))+' pct='+f'{100*len(proved)/len(inter):.2f}%')
lines.append('need_named_at_90pct='+str(-(-(9*len(inter))//10))+' buffer_over_92='+str(len(names)-92))
lines.append('outside_atlas='+' '.join(a.upper() for a in outside))
lines.append('UNNAMED ('+str(len(unnamed))+'):')
for a in unnamed:
    r=inter[a]
    lines.append(f"  {a.upper()}\tgrade_col5={r.get('grade','')}\tname={r.get('name','')}\tsize={atl[a].get('size','')}\tncallers={atl[a].get('n_callers','')}")
lines.append('NAMED_SORTED:')
for a in names: lines.append('  '+a.upper()+'\t'+inter[a].get('name',''))
text='\n'.join(lines)+'\n'
os.makedirs(OUT+r'\EVIDENCE',exist_ok=True)
open(OUT+r'\EVIDENCE\t0_baseline.txt','w',encoding='utf-8').write(text)
print(text)
