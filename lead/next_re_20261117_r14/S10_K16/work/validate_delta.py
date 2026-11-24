
import sys,os,re,csv,collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.dirname(__file__))
import common,k16
ROOT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K16'
DELTA=os.path.join(ROOT,'coverage_delta.tsv')
with open(DELTA,'r',encoding='utf-8',newline='') as f: rows=list(csv.reader(f,delimiter='\t'))
forbidden={'006FCDB0','004D7330','0051D6F0','0051DAF0','0051B1F0','00522340','006FB170','006FB470'}
ring4={'00701410':[0x007509E0],'0070B570':[0x004C93D0],'006F4EB0':[0x005657A0,0x007C8B3D]}
errs=[]
if len(rows)!=3: errs.append('rowcount '+str(len(rows)))
for r in rows:
 if len(r)!=9: errs.append('cols '+repr(r[0])+' '+str(len(r))); continue
 a,sub,name,sem,grade,path,ns,conf,kind=r
 if not re.fullmatch(r'[0-9A-F]{8}',a): errs.append('entry '+a)
 if a in forbidden: errs.append('forbidden '+a)
 if grade!='[静态推断]': errs.append('grade '+a+' '+grade)
 if not ns.isdigit() or int(ns)<1: errs.append('ns '+a)
 if conf!='0': errs.append('conflict '+a)
 if kind!='behavioral': errs.append('kind '+a)
 if re.search(r'(^|::)(sub_|slot\d+|vslot\d+)',name): errs.append('placeholder '+a+' '+name)
 p=os.path.join(ROOT,path.split('#')[0])
 if not os.path.exists(p): errs.append('missing evidence '+p)
 if '#'+a not in open(p,encoding='utf-8').read(): errs.append('missing anchor '+a)
 cr=k16.row(int(a,16))
 if not cr or cr[1]!='S10': errs.append('not S10/atlas '+a)
ins=[r[0] for r in rows]; nms=[r[2] for r in rows]
if len(set(ins))!=len(ins): errs.append('dup entries')
if len(set(nms))!=len(nms): errs.append('dup names')
for a,cs in ring4.items():
 size=next((int(r[1]) for k,r in k16.atl.items() if k==a.lower()),0)
 calls=[t for s,t in k16.direct_calls_in(int(a,16),size)]
 for c in cs:
  n=calls.count(c)
  if n<1: errs.append('ring4 not called %s -> %08X count=%d'%(a,c,n))
  cr=k16.row(c)
  if not cr or cr[4]!='[已证]': errs.append('ring4 grade %08X %s'%(c,repr(cr)))
for a in ['00701410','0070B570','006F4EB0']:
 p=os.path.join(ROOT,'EVIDENCE','PROOF_'+a+'.txt')
 t=open(p,encoding='utf-8').read()
 if 'match=False' in t: errs.append('raw mismatch '+a)
print('rows',len(rows),'cols',sorted(set(len(r) for r in rows)),'entries',ins,'kinds',sorted(set(r[8] for r in rows)))
print('ring4 called+grade: PASS' if not any(e.startswith('ring4') for e in errs) else 'ring4 FAIL')
print('RESULT','PASS' if not errs else 'FAIL')
for e in errs: print(' ERR',e)
open(os.path.join(ROOT,'EVIDENCE','DELTA_VALIDATE.txt'),'w',encoding='utf-8').write('rows %d cols %s entries %s kinds %s\nRESULT %s\n'%(len(rows),sorted(set(len(r) for r in rows)),ins,sorted(set(r[8] for r in rows)),'PASS' if not errs else 'FAIL')+'\n'.join('ERR '+e for e in errs)+'\n')
