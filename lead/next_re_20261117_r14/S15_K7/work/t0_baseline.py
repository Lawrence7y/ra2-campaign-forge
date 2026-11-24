# -*- coding: utf-8 -*-
from pathlib import Path
import re, math, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge'); R14=ROOT/'lead'/'next_re_20261117_r14'
COV=R14/'COVERAGE'/'coverage.tsv'; ATL=ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'
BIN=ROOT/'ra2youli'/'gamemd.exe'
NEW=['006E6310','006F1920','00727AA0']
def read(p):
    return [x.rstrip('\r\n').split('\t') for x in p.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
def norm(e): return e.strip().upper().zfill(8)
def named(n):
    n=(n or '').strip()
    return bool(n) and not n.lower().startswith('sub_') and not re.match(r'^[^:]+::sub_[0-9a-fA-F]+$',n)
atlas={norm(r[0]) for r in read(ATL) if r and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip())}
cov=[r for r in read(COV) if len(r)>4 and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and r[1].strip()=='S15']
base=sorted({norm(r[0]) for r in cov} & atlas)
bn={norm(r[0]) for r in cov if norm(r[0]) in base and named(r[2])}
bp={norm(r[0]) for r in cov if norm(r[0]) in base and r[4].strip()=='[已证]'}
mn=set(bn)|set(NEW); mp=set(bp)
need=math.ceil(0.9*len(base))
print('SHA256',hashlib.sha256(BIN.read_bytes()).hexdigest().upper())
print('size',BIN.stat().st_size)
print('S15_cov_rows',len(cov),'atlas_n',len(base),'need',need)
print('base_named',len(bn),'base_proved',len(bp))
print('live_named',len(bn),'pct',format(100*len(bn)/len(base),'.2f'),'shortfall',need-len(bn))
print('live_proved',len(bp),'pct',format(100*len(bp)/len(base),'.2f'))
print('delta_new',len(NEW),'post_named',len(mn),'pct',format(100*len(mn)/len(base),'.2f'),'post_shortfall',need-len(mn))
resid=[e for e in base if e not in mn]
print('resid_count',len(resid))
print('resid',','.join(resid))
