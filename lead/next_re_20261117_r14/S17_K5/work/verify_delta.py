from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib, os, re
CARD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=r'D:\Project\ra2-campaign-forge'
COV=ROOT+r'\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL=ROOT+r'\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EXE=ROOT+r'\ra2youli\gamemd.exe'
DELTA=CARD+r'\coverage_delta.tsv'
def norm(a): return a.strip().lower()
def rows(path,sep,header_sep=None):
 raw=open(path,'r',encoding='utf-8-sig').read().splitlines()
 hdr=raw[0].split(header_sep or sep); out=[]
 for ln in raw[1:]:
  if not ln.strip():continue
  p=ln.split(sep); p+=['']*(len(hdr)-len(p)) if len(p)<len(hdr) else []
  out.append(dict(zip(hdr,p)))
 return out
cov={norm(r['entry']):r for r in rows(COV,'\t',',')}
atl={norm(r['entry']):r for r in rows(ATL,'\t')}
s17={a:r for a,r in cov.items() if r.get('subsystem')=='S17' and a in atl}
def named(name):
 n=(name or '').strip()
 return bool(n) and not n.startswith('sub_') and not re.search(r'::sub_[0-9A-Fa-f]{6,8}$',n)
def stats(m=None):
 c=dict(s17)
 if m:
  for e,d in m.items():
   d0=dict(c.get(e,{})); d0.update(d); c[e]=d0
 den=len(c); nm=sum(1 for r in c.values() if named(r.get('name','')))
 pv=sum(1 for r in c.values() if r.get('grade','').strip()=='[已证]')
 return den,nm,pv
delta={}
for ln in open(DELTA,'r',encoding='utf-8').read().splitlines():
 if not ln.strip():continue
 p=ln.split('\t'); assert len(p)==9, (len(p),p)
 delta[norm(p[0])]={'subsystem':p[1],'name':p[2],'grade':p[4]}
h=hashlib.sha256(); h.update(open(EXE,'rb').read())
lines=[]
lines.append('S17_K5 final recomputation')
lines.append('time_asia_shanghai='+datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'))
lines.append('exe_sha256='+h.hexdigest().upper())
lines.append('delta_columns=9; delta_rows='+str(len(delta)))
for label,m in [('disk',None),('after_delta',delta)]:
 den,nm,pv=stats(m)
 lines.append(f'{label}: atlas_n={den} named={nm} ({100*nm/den:.2f}%) proved={pv} ({100*pv/den:.2f}%) buffer_over_92={nm-92}')
lines.append('need_named_90pct=92')
txt='\n'.join(lines)+'\n';open(CARD+r'\EVIDENCE\final_recompute.txt','w',encoding='utf-8').write(txt);print(txt)
