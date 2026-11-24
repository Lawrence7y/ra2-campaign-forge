# -*- coding: utf-8 -*-
from pathlib import Path
import re,sys,math,hashlib
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge'); R14=ROOT/'lead'/'next_re_20261117_r14'
COV=R14/'COVERAGE'/'coverage.tsv'; ATL=ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'; BIN=ROOT/'ra2youli'/'gamemd.exe'
def rows(p):
 return [x.rstrip('\r\n').split('\t') for x in p.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
def norm(e): return e.strip().upper().zfill(8)
def named(n):
 n=(n or '').strip(); return bool(n) and not n.lower().startswith('sub_') and not re.match(r'^[^:]+::sub_[0-9a-fA-F]+$',n)
atlas={norm(r[0]):int(r[1]) for r in rows(ATL) if r and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and len(r)>1 and r[1].strip().isdigit()}
cov=[r for r in rows(COV) if len(r)>4 and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip())]
base=sorted({norm(r[0]) for r in cov if r[1].strip()=='S13'} & set(atlas))
recs=[]
for r in cov:
 e=norm(r[0])
 if e in base and r[1].strip()=='S13': recs.append(dict(e=e,size=atlas[e],name=r[2].strip(),sem=r[3].strip(),grade=r[4].strip(),ev=r[5].strip(),ns=r[6].strip(),conf=r[7].strip() if len(r)>7 else ''))
bn=[r for r in recs if named(r['name'])]; bp=[r for r in recs if r['grade']=='[已证]']
print('SHA256',hashlib.sha256(BIN.read_bytes()).hexdigest().upper())
print('S13_rows',len([r for r in cov if r[1].strip()=='S13']),'atlas_n',len(base),'named',len(bn),'proved',len(bp),'need',math.ceil(.5*len(base)),'shortfall',math.ceil(.5*len(base))-len(bp))
print('grade_counts')
from collections import Counter
print(Counter(r['grade'] for r in recs))
print('named_not_proved',len([r for r in bn if r['grade']!='[已证]']))
print('name_classes')
for r in bn:
 if r['grade']!='[已证]': print(r['e'],r['size'],r['name'],r['grade'],r['sem'][:100])
