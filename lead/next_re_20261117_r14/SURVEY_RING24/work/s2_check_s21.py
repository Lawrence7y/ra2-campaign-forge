
import json,collections,re
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
idx=json.load(open(OUT/'work'/'index.json'))
vt=idx['vtables']; e2s={int(k,16):v for k,v in idx['entry2slots'].items()}
direct={int(k,16):v for k,v in idx['direct'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
cls=collections.Counter(vt.values())
print('distinct class names', len(cls))
print('top classes', cls.most_common(8))
# S21 validation
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATLAS=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
lines=COV.read_text(encoding='utf-8-sig').splitlines()
hdr=lines[0].split(',')
cov=[]
for l in lines[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(8-len(q)); cov.append(dict(zip(hdr,q[:8])))
al=ATLAS.read_text(encoding='utf-8-sig').splitlines(); ah=al[0].split('\t')
atlas={}
for l in al[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(len(ah)-len(q)); r=dict(zip(ah,q[:len(ah)]))
    atlas[r['entry'].strip().upper().replace('0X','')]=r
def norm(e): return e.strip().upper().replace('0X','')
s21=[r for r in cov if r['subsystem'].strip().upper()=='S21' and r['grade'].strip()=='[静态推断]' and norm(r['entry']) in atlas]
print('S21 static rows', len(s21))
h2=0;h4=0;both=0;neither=0
for r in s21:
    e=int(norm(r['entry']),16)
    a=bool(e2s.get(e)); b=bool(direct.get(e)) or bool(livevt.get(e))
    if a and b: both+=1
    elif a: h2+=1
    elif b: h4+=1
    else: neither+=1
print('S21: 2only',h2,'4only',h4,'both',both,'neither',neither)
