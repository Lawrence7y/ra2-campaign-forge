from __future__ import annotations
import hashlib,math,os,re
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=r'D:\Project\ra2-campaign-forge'
COV=ROOT+r'\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL=ROOT+r'\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EXE=ROOT+r'\ra2youli\gamemd.exe'
CARD=ROOT+r'\lead\next_re_20261117_r14\S17_K6'
def norm(a):return a.strip().lower()
def load(path,sep,header_sep=None):
 raw=open(path,'r',encoding='utf-8-sig').read().splitlines(); hdr=raw[0].split(header_sep or sep); out=[]
 for ln in raw[1:]:
  if not ln.strip():continue
  p=ln.split(sep); p+=['']*(len(hdr)-len(p)); out.append(dict(zip(hdr,p)))
 return out
cov={norm(r['entry']):r for r in load(COV,'\t',',')}
atl={norm(r['entry']):r for r in load(ATL,'\t')}
s17={a:r for a,r in cov.items() if r.get('subsystem','').strip().upper()=='S17' and a in atl}
def named(r):
 n=(r.get('name') or '').strip()
 return bool(n) and not n.startswith('sub_') and not re.search(r'::sub_[0-9A-Fa-f]{6,8}$',n)
def stats(d):
 n=len(d); nm=sum(1 for r in d.values() if named(r)); pv=sum(1 for r in d.values() if r.get('grade','').strip()=='[已证]')
 return n,nm,pv,math.ceil(0.9*n),nm-math.ceil(0.9*n)
delta={}
for ln in open(CARD+r'\coverage_delta.tsv','r',encoding='utf-8').read().splitlines():
 if not ln.strip():continue
 p=ln.split('\t'); assert len(p)==9
 delta[norm(p[0])]={'subsystem':p[1],'name':p[2],'grade':p[4],'name_kind':p[8]}
def merged(remove=(),extra=()):
 d={a:dict(r) for a,r in s17.items()}
 for a in remove:d.pop(a,None)
 for a,r in extra.items():
  x=dict(d.get(a,{})); x.update(r); d[a]=x
 return d
h=hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper()
t=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
base_stats=stats(s17)
k5={'004068e0':{'name':'DebugLogSink_behavior','grade':'[静态推断]','subsystem':'S17'}}
scenarios=[
 ('disk',s17),
 ('k6_only',merged(extra=delta)),
 ('k5_plus_k6_keep_4068e0',merged(extra={**k5,**delta})),
 ('remove_4068e0_plus_k6',merged(remove=('004068e0',),extra=delta)),
]
lines=['S17-K6 baseline/final recomputation','time_asia_shanghai='+t,'exe_sha256='+h,'exe_bytes='+str(os.path.getsize(EXE))]
lines.append('delta_columns=9; delta_rows='+str(len(delta))+' delta_entries='+' '.join(sorted(a.upper() for a in delta)))
lines.append('unnamed_on_disk='+str(sum(1 for r in s17.values() if not named(r))))
for label,d in scenarios:
 n,nm,pv,need,buf=stats(d)
 lines.append(f'{label}: atlas_n={n} named={nm} ({100*nm/n:.2f}%) proved={pv} ({100*pv/n:.2f}%) need_90pct={need} buffer={buf}')
base_txt='\n'.join(lines)+'\n'
open(CARD+r'\EVIDENCE\baseline_recompute.txt','w',encoding='utf-8').write(base_txt)
open(CARD+r'\EVIDENCE\final_recompute.txt','w',encoding='utf-8').write(base_txt)
print(base_txt)
