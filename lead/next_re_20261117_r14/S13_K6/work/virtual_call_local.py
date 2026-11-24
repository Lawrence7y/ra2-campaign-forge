# -*- coding: utf-8 -*-
import sys,re,struct
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge');R14=ROOT/'lead'/'next_re_20261117_r14'
def rows(path): return [x.rstrip('\r\n').split('\t') for x in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
atlas={}
for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'):
 if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and r[1].strip().isdigit(): atlas[int(r[0],16)]=int(r[1])
cov=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
 if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()): cov.append((int(r[0],16),r[1].strip(),r[2].strip(),r[4].strip()))
def owner(site):
 for a,s,n,g in cov:
  sz=atlas.get(a,0)
  if sz and a<=site<a+sz: return f'{a:08X}/{s}/{g}/{n}'
 return 'OUTSIDE'
VTS={0x7E17CC:'Bomb',0x7E1E84:'Warhead',0x7E1ED4:'Weapon',0x7E4678:'Bullet',0x7E5170:'UDamage',0x7ECE7C:'Kamikaze',0x7EF824:'Parasite',0x7F07A4:'RadSite'}
for vt,label in VTS.items():
 refs=[x for x in p.imm_refs(vt) if p.TSTART<=x<p.TEND]
 gl=set()
 for s in refs:
  for a,bb,txt,i in p.dis(max(p.TSTART,s-16),0x30):
   if a<=s<a+len(bytes.fromhex(bb)) and txt.startswith('mov dword ptr ['):
    mm=re.match(r'mov dword ptr \[(0x[0-9a-f]+)\]',txt)
    if mm: gl.add(int(mm.group(1),16))
 print(f'\n=== {label} VT {vt:#x} globals {[hex(x) for x in sorted(gl)]} ===')
 for g in sorted(gl):
  xs=p.imm_refs(g); xs=[x for x in xs if p.TSTART<=x<p.TEND]
  print(f'-- G {g:#x} xrefs {len(xs)} {[hex(x) for x in xs]}')
  found=[]
  for s in xs:
   for a,bb,txt,i in p.dis(max(p.TSTART,s-16),0x120):
    if txt.startswith('call dword ptr ['):
     z=re.search(r'\+ (0x[0-9a-f]+|\d+)\]',txt)
     if z:
      off=int(z.group(1),0)
      if 0<=off<=0x18 and off%4==0 and s-0x40<=a<=s+0xc0:
       found.append((a,off//4,txt,owner(a)))
  for a,sl,txt,ow in sorted(set(found)): print(f'   vc {a:08X} slot{sl} [{txt}] owner={ow}')
