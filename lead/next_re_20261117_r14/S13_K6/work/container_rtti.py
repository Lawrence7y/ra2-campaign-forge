# -*- coding: utf-8 -*-
import sys,re,struct
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge');R14=ROOT/'lead'/'next_re_20261117_r14'
def rows(path): return [x.rstrip('\r\n').split('\t') for x in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
atlas={int(r[0],16):int(r[1]) for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv') if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip())}
rec=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
 if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()) and r[1].strip()=='S13':
  e=int(r[0],16);m=re.search(r'(?P<kind>(?:T_)?(?:DynamicVectorClass|VectorClass)|\?\$DynamicVectorClass|\?\$VectorClass).*?(?:vslot|slot)(?P<slot>\d+)',r[2])
  if m:
   kind='DYNAMIC' if 'Dynamic' in r[2] else 'VECTOR'; slot=int(m.group('slot'))
   rec.append((e,atlas[e],r[2].strip(),kind,slot))
print('container_rows',len(rec))
# valid virtual VA mapping helper
def off2va(o):
 for sn,sva,vs,rs,ro in p.SECS:
  if ro<=o<ro+rs:
   delta=o-ro
   if delta<vs: return sva+delta
 return None
def fmtname(b):
 z=b.find(0);return (b[:z] if z>=0 else b).decode('latin1')
for e,sz,name,kind,slot in sorted(rec):
 pat=struct.pack('<I',e);sites=[];pos=0
 while True:
  j=p.data.find(pat,pos)
  if j<0:break
  va=off2va(j)
  if va is not None and va>=p.IB: sites.append(va)
  pos=j+1
 infos=[]
 for va in sites:
  vt=va-slot*4
  try:
   info=p.vtinfo(vt); nm=fmtname(info['name'])
   infos.append((va,vt,nm))
  except Exception: pass
 print(f'{e:08X}\t{name}\tptrs={[hex(x) for x in sites][:10]}\trtti={infos[:10]}')
