# -*- coding: utf-8 -*-
import sys,re,hashlib
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge');R14=ROOT/'lead'/'next_re_20261117_r14'
def rows(path): return [x.rstrip('\r\n').split('\t') for x in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
atlas={int(r[0],16):int(r[1]) for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv') if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and r[1].strip().isdigit()}
rec=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
 if len(r)>4 and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and r[1].strip()=='S13':
  e=int(r[0],16); name=r[2].strip()
  m=re.search(r'(?:vslot|slot)(\d+)',name)
  if m and 'DynamicVectorClass' in name: rec.append((e,atlas[e],int(m.group(1)),name))
print('dynamic_rows',len(rec))
from collections import defaultdict
by=defaultdict(list)
for e,sz,sl,name in sorted(rec):
 ins=p.dis(e,sz)
 # normalize operands: replace all hex immediates and memory displacements with #, keep register/mnemonic
 norm=[]
 for a,bb,txt,i in ins:
  m=txt.split(' ',1); op=m[1] if len(m)>1 else ''
  op=re.sub(r'0x[0-9a-f]+','#',op); op=re.sub(r'\[[^]]*\]','[M]',op)
  op=re.sub(r'\b[a-z][a-z0-9]*\b(?=#)','R',op)
  norm.append(m[0]+' '+op)
 h=hashlib.sha256(('\n'.join(norm)).encode()).hexdigest()[:12]
 by[sl].append((e,sz,h,name,ins))
 print(f'{e:08X}\tslot{sl}\tsize={sz}\thash={h}\tins={len(ins)}\tname={name}')
print('\nSLOT_BASELINE')
for sl in sorted(by):
 sizes=sorted(set(x[1] for x in by[sl])); hs=sorted(set(x[2] for x in by[sl]))
 print(f'slot{sl}: rows={len(by[sl])} sizes={sizes} hashes={hs}')
