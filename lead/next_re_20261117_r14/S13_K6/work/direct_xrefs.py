# -*- coding: utf-8 -*-
import sys,re,struct
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge');R14=ROOT/'lead'/'next_re_20261117_r14'
def rows(path): return [x.rstrip('\r\n').split('\t') for x in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
atlas={int(r[0],16):int(r[1]) for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv') if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip())}
cov=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
 if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()) and r[1].strip()=='S13':
  e=int(r[0],16)
  if e in atlas and ('vslot' in r[2] or ('VectorClass' in r[2] and 'slot' in r[2])): cov.append((e,atlas[e],r[2],r[4]))
blob=p.data[p.TEXT.PointerToRawData:p.TEXT.PointerToRawData+p.TEXT.Misc_VirtualSize]
def e8sites(target):
 out=[];i=0
 while True:
  j=blob.find(b'\xe8',i)
  if j<0:break
  rel=struct.unpack_from('<i',blob,j+1)[0];site=p.TSTART+j
  if site+5+rel==target: out.append(site)
  i=j+1
 return out
for e,sz,name,grade in sorted(cov):
 sites=e8sites(e)
 print(f'{e:08X}\t{name}\tgrade={grade}\tE8={[hex(x) for x in sites][:12]}')
