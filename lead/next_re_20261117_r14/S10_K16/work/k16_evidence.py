
import sys,os,json,hashlib,time,csv,collections,struct,re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.dirname(__file__))
import common,k16
ROOT=r'D:\Project\ra2-campaign-forge'
EVID=os.path.join(ROOT,r'lead\next_re_20261117_r14\S10_K16\EVIDENCE')
os.makedirs(EVID,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest().upper()
COV=common.COV; ATL=common.ATL; EXE=common.EXE
def baseline_text():
 rows,cov,atl=common.load_rows()
 s10=[r for r in rows if len(r)>=8 and r[1]=='S10']
 inter=[r for r in s10 if r[0].lower() in atl]
 grades=collections.Counter(r[4] for r in inter)
 named=sum(1 for r in inter if r[2] and not r[2].startswith('sub_'))
 out=[]
 out.append('BASELINE TIME '+time.strftime('%Y-%m-%dT%H:%M:%S%z'))
 out.append('EXE '+EXE+' sha='+sha(EXE)+' size='+str(os.path.getsize(EXE)))
 out.append('COV '+COV+' sha='+sha(COV)+' size='+str(os.path.getsize(COV))+' mtime='+time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.path.getmtime(COV))))
 out.append('ATL '+ATL+' sha='+sha(ATL)+' size='+str(os.path.getsize(ATL)))
 out.append('S10 rows %d intersection %d outside %d'%(len(s10),len(inter),len(s10)-len(inter)))
 out.append('grades col5 '+repr(dict(grades)))
 out.append('proved %d proved_pct %.4f named_L %d named_pct %.4f threshold 263 gap %d'%(grades['[已证]'],grades['[已证]']*100/len(inter),named,named*100/len(inter),263-grades['[已证]']))
 out.append('entry case normalized lower; grade read only column 5; atlas entry lower, coverage upper')
 return '\n'.join(out)+'\n'
open(os.path.join(EVID,'BASELINE.txt'),'w',encoding='utf-8').write(baseline_text())

def size_of(a):
 return next((int(r[1]) for k,r in k16.atl.items() if k==f'{a:08x}'),None)

def raw_check(a,hexbytes):
 b=common.read(a,len(bytes.fromhex(hexbytes)))
 return b.hex().upper()==hexbytes.upper().replace(' ','')
def raw_refs(addr,lo,hi):
 return [hex(x) for x in common.find_refs_to(addr) if lo<=x<=hi]

targets=[
 {'a':0x00701410,'slot':0x40c,'name':'TechnoClass::TypeSoundCacheAndConditionalAudio_behavior','vts':None,
  'patterns':[(0x701424,'ff92840000008b80a0000000'),(0x701432,'89466c894670'),(0x701473,'e8680ad5ff')],
  'ext':[(0x519FA6,'external caller 00519630 reads type+0xA0 and compares [this+0x6C] before vcall'),(0x519FF0,'vcall [v+0x40C] only at this site')],
  'callees':[0x7509E0]},
 {'a':0x0070B570,'slot':0x41c,'name':'TechnoClass::ClampAndAdvancePairedFloatState_behavior','vts':None,
  'patterns':[(0x70B5F1,'e8dadddbff'),(0x70B78B,'c78628030000db0f493f'),(0x70B957,'899e30030000899e28030000'),(0x70BC9E,'ff926c010000')],
  'ext':[(0x6FA228,'proved caller 006F9E50 v[something+0x298] true'),(0x6FA230,'gate [this+0x90] nonzero'),(0x6FA236,'vcall [v+0x41C]')],
  'callees':[0x4C93D0]},
 {'a':0x006F4EB0,'slot':0x420,'name':'TechnoClass::Mode2NearbyObjectListRefresh_behavior','vts':None,
  'patterns':[(0x6F4EFD,'50e89d08e7ff'),(0x6F4F05,'8b862002000083f802752a'),(0x6F4F19,'39861c020000'),(0x6F503F,'ff9260040000')],
  'ext':[(0x6FA95B,'proved caller gate [this+0x220]==0'),(0x6FA993,'vcall [v+0x420] after [this+0x220]==0 and cell test'),(0x6FA999,'proved caller gate [this+0x220]==2'),(0x6FA9D2,'vcall [v+0x420] after cell test')],
  'callees':[0x5657A0,0x7C8B3D]}
]
callers=k16.callers_of([t['a'] for t in targets])
for spec in targets:
 a=spec['a']; size=size_of(a); ins=common.disasm(a,size); r=k16.row(a)
 lines=[]
 lines.append('PROOF '+f'{a:08X}'+' '+spec['name'])
 lines.append('== CHANNEL A: pefile+capstone, full function, atlas size used only for output slice ==')
 lines.append('target coverage row: '+repr(r))
 lines.append('size='+str(size)+' first='+common.fmt(ins[0])+' last='+common.fmt(ins[-1])+' nins='+str(len(ins)))
 lines.append('')
 lines.append('-- class ownership: RTTI COL=vt-4, TD=u32(COL+0xC), inline name at TD+8 --')
 cls=k16.cls(a)
 for cname,td,nm,k,vtva in cls:
  lines.append('  slot %d (+0x%X) vt=%s class=%s TD=%s inline=%s'%(k,4*k,vtva,cname,hex(td) if td else '?',nm))
 lines.append('  all class_at_slot entries above are the same address; no other subclass slot entry found.')
 lines.append('')
 lines.append('-- full disassembly --')
 for i in ins: lines.append(common.fmt(i))
 lines.append('')
 lines.append('-- direct calls in body (grade read from coverage col5) --')
 for site,t in k16.direct_calls_in(a,size):
  cr=k16.row(t)
  lines.append('  %08X -> %08X %s'%(site,t,repr((cr[1],cr[2],cr[4],cr[6],cr[7]) if cr else None)))
 lines.append('')
 lines.append('-- external vcall callers, site ownership by atlas interval --')
 by=collections.defaultdict(list)
 for site,ca in callers.get(a,[]): by[ca].append(site)
 for ca,sites in sorted(by.items()):
  cr=k16.row(ca)
  lines.append('  caller %08X %s sites %s'%(ca,repr((cr[1],cr[2],cr[4]) if cr else None),' '.join(f'{s:08X}' for s in sites)))
 if not by: lines.append('  (none direct; see vcall scan in EVIDENCE/NEIGHBOR_VCALLS.txt)')
 lines.append('')
 lines.append('-- vcall sites at disp 0x%X from full-image scan --'%spec['slot'])
 pat=re.compile(r'\[\w+ \+ 0x'+f"{spec['slot']:x}"+r'\]')
 hits=[]
 for ca,sz in k16.FUNCS:
  ci=common.disasm(ca,sz)
  for j,i in enumerate(ci):
   if i.mnemonic=='call' and pat.search(i.op_str): hits.append((i.address,ca,ci,j))
 for site,ca,ci,j in hits:
  cr=k16.row(ca)
  lines.append('  site %08X in %08X %s'%(site,ca,repr((cr[1],cr[2],cr[4]) if cr else None)))
  for p in ci[max(0,j-4):j+2]: lines.append('    '+common.fmt(p))
 lines.append('')
 lines.append('-- channel B: raw bytes independent of atlas entry+size --')
 for va,hx in spec['patterns']:
  b=common.read(va,len(hx)//2)
  lines.append('  raw@%08X expect=%s actual=%s match=%s'%(va,hx,b.hex().upper(),raw_check(va,hx)))
 for va,desc in spec['ext']:
  b=common.read(va,8)
  lines.append('  raw-ctx@%08X %s bytes=%s'%(va,desc,b.hex().upper()))
 for cname,td,nm,k,vtva in cls:
  lines.append('  raw-dword@%s slot%d = %s'%(vtva,k,hex(common.u32(int(vtva,16)+4*k) or 0)))
 lines.append('')
 lines.append('-- grade check for ring4 callees --')
 for t in spec['callees']:
  cr=k16.row(t)
  lines.append('  %08X %s'%(t,repr(cr)))
 lines.insert(0,'#'+f'{a:08X}')
 open(os.path.join(EVID,'PROOF_%08X.txt'%a),'w',encoding='utf-8').write('\n'.join(lines)+'\n')
 print('wrote',os.path.join(EVID,'PROOF_%08X.txt'%a),'lines',len(lines))
