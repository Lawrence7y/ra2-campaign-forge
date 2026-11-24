# -*- coding: utf-8 -*-
import sys,re,struct,collections
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge');R14=ROOT/'lead'/'next_re_20261117_r14'
def rows(path):
 return [x.rstrip('\r\n').split('\t') for x in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
atlas={int(r[0],16):int(r[1]) for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv') if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip())}
rec=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
 if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()) and r[1].strip()=='S13' and ('vslot' in r[2] or 'VectorClass' in r[2]):
  e=int(r[0],16); m=re.search(r'(?P<kind>DynamicVectorClass|VectorClass).*?vslot(?P<slot>\d+)',r[2])
  if m: rec.append((e,atlas[e],r[2].strip(),m.group('kind'),int(m.group('slot'))))
print('container_rows',len(rec))
# find exact pointer occurrences anywhere in image-mapped raw bytes
for e,sz,name,kind,slot in sorted(rec):
 pat=struct.pack('<I',e); sites=[]; pos=0
 while True:
  j=p.data.find(pat,pos)
  if j<0: break
  rva=j
  # convert raw offset to VA if possible only if inside section raw range
  for sn,sva,vs,rs,ro in p.SECS:
   if ro<=j<ro+rs:
    va=p.IB+sva+(j-ro)
    if va>=p.TSTART and va<p.TEND: pass
    sites.append((va,sva+(j-ro),sn))
  pos=j+1
 infos=[]
 for va,rva,sn in sites:
  vt=va-slot*4
  try:
   info=p.vtinfo(vt)
   if info['name'].startswith(b'.?$') or b'Vector' in info['name'] or b'T_Dynamic' in info['name']:
    infos.append((sn,va,vt,info['name'].decode('latin1')))
  except Exception: pass
 print(f'{e:08X}\t{name}\tptrs={[hex(x[0]) for x in sites][:8]}\trtti={infos[:8]}')
