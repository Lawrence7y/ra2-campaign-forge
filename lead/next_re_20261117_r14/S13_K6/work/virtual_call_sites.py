# -*- coding: utf-8 -*-
import sys,re
from pathlib import Path
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge');R14=ROOT/'lead'/'next_re_20261117_r14'
def rows(path): return [x.rstrip('\r\n').split('\t') for x in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()]
cov=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
 if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()): cov.append((int(r[0],16),int(r[1]) if False else r[1].strip(),r[2].strip(),r[4].strip()))
atlas={}
for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'):
 if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and r[1].strip().isdigit(): atlas[int(r[0],16)]=int(r[1])
def owner(site):
 for a,s,n,g in cov:
  sz=atlas.get(a,0)
  if sz and a<=site<a+sz: return (f'{a:08X}',s,n,g,sz)
 return None
INS=[(i.address,i.bytes.hex(),i.mnemonic,i.op_str) for i in p.MD.disasm(p.rd(p.TSTART,p.TEXT.Misc_VirtualSize),p.TSTART)]
VTS={0x7E17CC:'Bomb',0x7E1E84:'Warhead',0x7E1ED4:'Weapon',0x7E4678:'Bullet',0x7E5170:'UDamage',0x7ECE7C:'Kamikaze',0x7EF824:'Parasite',0x7F07A4:'RadSite'}
for vt,label in VTS.items():
 refs=[x for x in p.imm_refs(vt) if p.TSTART<=x<p.TEND]
 globals=[]
 for s in refs:
  for a,bb,m,o in INS:
   if a<=s<a+len(bytes.fromhex(bb)) and m=='mov' and o.startswith('dword ptr ['):
    mm=re.match(r'dword ptr \[(0x[0-9a-f]+)\]',o)
    if mm: globals.append((int(mm.group(1),16),a))
 print(f'\n=== {label} VT {vt:#x} globals {[(hex(g),hex(a)) for g,a in globals]} ===')
 for g,init in globals:
  xrefs=[]
  for a,bb,m,o in INS:
   try:
    if f'[{g:#x}]' in o or f'[0x{g:x}]' in o: xrefs.append((a,m,o))
   except: pass
  print(f'-- G {g:#x} xrefs {len(xrefs)}: {[hex(a) for a,_,_ in xrefs[:20]]}')
  for a,m,o in xrefs:
   for b,bb,mm,oo in INS:
    if a<=b<a+0x80 and mm=='call' and oo.startswith('dword ptr ['):
     z=re.search(r'\+ (0x[0-9a-f]+)\]',oo)
     if z:
      off=int(z.group(1),0); slot=off//4
      if 0<=slot<=6 and off%4==0:
       ow=owner(b)
       print(f'   vc {b:08X} slot{slot} [{mm} {oo}] owner={ow}')
