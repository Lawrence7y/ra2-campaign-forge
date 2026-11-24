# -*- coding: utf-8 -*-
import sys,struct,re
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
root=Path(r'D:\\Project\\ra2-campaign-forge'); R14=root/'lead'/'next_re_20261117_r14'
cov={}; atlas={}
for l in (R14/'COVERAGE'/'coverage.tsv').read_text(encoding='utf-8-sig').splitlines():
 c=l.split('\t')
 if len(c)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',c[0].strip()): cov[int(c[0],16)]=c
for l in (root/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv').read_text(encoding='utf-8-sig').splitlines():
 c=l.split('\t')
 if len(c)>1 and re.fullmatch(r'[0-9A-Fa-f]{8}',c[0].strip()) and c[1].strip().isdigit(): atlas[int(c[0],16)]=int(c[1].strip())
blob=p.data[p.TEXT.PointerToRawData:p.TEXT.PointerToRawData+p.TEXT.Misc_VirtualSize]
E8=bytes([0xe8])
for t in [0x6E6310,0x6F1920,0x727AA0]:
 print(f'\\n=== direct E8 call xrefs to {t:#x} ===')
 sites=[];i=0
 while True:
  j=blob.find(E8,i)
  if j<0: break
  site=p.TSTART+j
  rel=struct.unpack_from('<i',blob,j+1)[0]
  if site+5+rel==t: sites.append(site)
  i=j+1
 print('sites',[hex(x) for x in sites])
 for site in sites:
  owners=[]
  for a,c in cov.items():
   sz=atlas.get(a,0)
   if sz and a<=site<a+sz: owners.append((a,c[2],c[4],sz))
  print(f'-- site {site:#x} callers {owners} --')
  for a,bb,s,ins in p.dis(site-0x30,0x48):
   mark='<<<' if a==site else ''
   print(f'{a:08X}  {bb:<20s} {s} {mark}')
