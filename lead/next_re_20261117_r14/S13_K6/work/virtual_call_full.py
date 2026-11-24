# -*- coding: utf-8 -*-
import sys,re
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
def find_owner(site):
 for a,s,n,g in cov:
  sz=atlas.get(a,0)
  if sz and a<=site<a+sz: return a,s,n,g,sz
 return None,None,None,None,0
GLOBALS={0x89C668:'Bomb',0x8874C0:'Warhead',0x887568:'Weapon',0x89DE18:'Bullet',0xA8ED40:'Bullet',0xABC604:'Kamikaze',0xAC4910:'Parasite',0xB04BD0:'RadSite'}
for g,label in GLOBALS.items():
 xs=[x for x in p.imm_refs(g) if p.TSTART<=x<p.TEND]
 funcs={}
 for s in xs:
  a,sub,n,grade,sz=find_owner(s)
  if a: funcs[a]=(sub,n,grade,sz)
 print(f'\n=== {label} G {g:#x} funcs {len(funcs)} ===')
 for a,(sub,n,grade,sz) in sorted(funcs.items()):
  calls=[]
  for aa,bb,txt,i in p.dis(a,min(sz+0x40,0x2000)):
   if txt.startswith('call dword ptr ['):
    z=re.search(r'\+ (0x[0-9a-f]+|\d+)\]',txt)
    if z:
     off=int(z.group(1),0)
     if 0<=off<=0x18 and off%4==0: calls.append((aa,off//4,txt))
  if calls:
   print(f'  fn {a:08X} {sub} {grade} {n} calls {[(hex(x),s) for x,s,_ in calls]}')
