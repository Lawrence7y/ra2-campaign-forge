import os,csv,hashlib,struct,collections,random,json,bisect,re
import capstone,pefile
ROOT='D:/Project/ra2-campaign-forge'; OUT=ROOT+'/lead/next_re_20261117_r14/S10_KPROVED'; WORK=OUT+'/work'; EV=OUT+'/EVIDENCE'
os.makedirs(WORK,exist_ok=True); os.makedirs(EV,exist_ok=True)
EXE=ROOT+'/ra2youli/gamemd.exe'; B=open(EXE,'rb').read(); PE=pefile.PE(EXE,fast_load=True); BASE=PE.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in PE.sections:
 nm=s.Name.rstrip(b'\x00').decode(errors='replace'); va=BASE+s.VirtualAddress; SECS.append((nm,va,va+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
def rd(va,n):
 for nm,a,z,raw,sz in SECS:
  if a<=va<z:
   o=raw+(va-a); return B[o:o+n] if 0<=o and o+n<=len(B) else None
 return None
def u32(va):
 x=rd(va,4); return struct.unpack('<I',x)[0] if x and len(x)==4 else None
T=[s for s in SECS if s[0]=='.text'][0]; _,TLO,THI,TRAW,TSZ=T
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
ALL=list(MD.disasm(B[TRAW:TRAW+TSZ],TLO))
REAL=[i for i in ALL if i.id!=0 and i.mnemonic!='data' and i.operands]
COVCOLS=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
COV=[dict(zip(COVCOLS,l.rstrip('\r\n').split('\t'))) for l in open(ROOT+'/lead/next_re_20261117_r14/COVERAGE/coverage.tsv',encoding='utf-8',errors='replace').read().splitlines()[1:] if l.strip()]
COVMAP={r['entry'].upper():r for r in COV}
ATL=[]
with open(ROOT+'/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv',encoding='utf-8',errors='replace',newline='') as f:
 ah=f.readline().strip().split('\t'); ATL=[dict(zip(ah,l.rstrip('\r\n').split('\t'))) for l in f if l.strip()]
AT={r['entry'].upper():r for r in ATL}
S10=[r for r in COV if r['subsystem'].strip().upper()=='S10' and r['entry'].upper() in AT]
STATIC=[r for r in S10 if r['grade']=='[静态推断]']; TARGETS={int(r['entry'],16):r for r in STATIC}
PROVED={int(k,16) for k,v in COVMAP.items() if v['grade']=='[已证]'}
IV=[]
for r in ATL:
 try: e=int(r['entry'],16); sz=int(r['size'])
 except: continue
 if TLO<=e<THI and sz>0: IV.append((e,min(THI,e+sz),r))
IV.sort(); STARTS=[x[0] for x in IV]
def owner_of(va):
 k=bisect.bisect_right(STARTS,va)-1
 while k>=0:
  a,z,r=IV[k]
  if a<=va<z: return r
  k-=1
 return None
# reverse pointer index in rdata/data for target entries
PTR=collections.defaultdict(list)
for secname in ['.rdata','.data']:
 nm,a,z,raw,sz=next((s for s in SECS if s[0]==secname), (None,0,0,0,0))
 for va in range(a,z-4,4):
  o=raw+(va-a)
  if o+4>len(B): break
  v=struct.unpack_from('<I',B,o)[0]
  if v in TARGETS: PTR[v].append(va)
TABSLOT=collections.defaultdict(list)
for t,addrs in PTR.items():
 for addr in addrs:
  for k in range(0,400):
   base=addr-4*k
   if 0x7e1000<=base<0x811074: TABSLOT[(base,k)].append(t)
TABLES=set(k[0] for k in TABSLOT)
VTREF=collections.defaultdict(list); DIRECT=collections.defaultdict(list)
for i in REAL:
 for o in i.operands:
  if o.type==capstone.x86.X86_OP_IMM and o.imm in TABLES: VTREF[o.imm].append(i.address)
 if i.mnemonic=='call' and i.operands[0].type==capstone.x86.X86_OP_IMM and i.operands[0].imm in TARGETS: DIRECT[i.operands[0].imm].append(i.address)
# vptr writes to table bases
WRITE=collections.defaultdict(list)
for idx,i in enumerate(REAL):
 if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM and i.operands[1].type==capstone.x86.X86_OP_IMM:
  v=i.operands[1].imm
  if v not in TABLES: continue
  op=i.operands[0].mem
  if op.base==0: WRITE[(op.disp,0,v)].append(('ABS',i.address))
  else:
   for j in range(max(0,idx-100),idx):
    p=REAL[j]
    if p.mnemonic=='mov' and len(p.operands)==2 and p.operands[0].type==capstone.x86.X86_OP_REG and p.operands[0].reg==op.base and p.operands[1].type==capstone.x86.X86_OP_IMM:
     g=p.operands[1].imm
     if 0x812000<=g<0xb79be4: WRITE[(g,op.disp,v)].append(('CTOR',p.address))
     break
# exact dispatch call sites: index writes by global for O(1) lookup
WB=collections.defaultdict(list)
for (g,off,vt),srcs in WRITE.items():
 WB[g].append((off,vt,srcs[0][0],srcs[0][1]))
EXACT=collections.defaultdict(list)
for idx,i in enumerate(REAL):
 if i.mnemonic!='call' or i.operands[0].type!=capstone.x86.X86_OP_MEM: continue
 op=i.operands[0].mem
 if op.base==0 or op.index!=0 or op.disp%4: continue
 g=None
 for j in range(idx-1,max(-1,idx-6),-1):
  p=REAL[j]
  if p.mnemonic=='mov' and len(p.operands)==2 and p.operands[0].type==capstone.x86.X86_OP_REG and p.operands[0].reg==op.base and p.operands[1].type==capstone.x86.X86_OP_MEM and p.operands[1].mem.base==0:
   g=p.operands[1].mem.disp; break
 if g is None: continue
 for wo,vt,src,ws in WB.get(g,[]):
  if wo!=0: continue
  t=u32(vt+op.disp)
  if t in TARGETS:
   EXACT[t].append((i.address,g,op.disp//4,vt,src,ws,i.mnemonic+' '+i.op_str))
# classify rows
C1=[]; C2=[]; PASS=set()
for e,r in sorted(TARGETS.items()):
 ds=[s for s in DIRECT.get(e,[]) if owner_of(s) and int(owner_of(s)['entry'],16)!=e]
 es=[x for x in EXACT.get(e,[]) if owner_of(x[0]) and int(owner_of(x[0])['entry'],16)!=e]
 slots=[(base,k) for (base,k),ts in TABSLOT.items() if e in ts]
 body_end=next((z for a,z,rr in IV if a==e),e); body=[i for i in REAL if e<=i.address<body_end]
 sha=hashlib.sha256(('|'.join(f'{i.mnemonic} {i.op_str}' for i in body)).encode()).hexdigest()[:12].upper()
 fw=[]; pc=[]
 for i in body:
  if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM and i.operands[0].mem.base!=0 and i.operands[1].type==capstone.x86.X86_OP_IMM:
   fw.append(f'{i.op_str}=0x{i.operands[1].imm & 0xffffffff:x}')
  if i.mnemonic=='call' and i.operands[0].type==capstone.x86.X86_OP_IMM and i.operands[0].imm in PROVED: pc.append(f'{i.operands[0].imm:08X}@{i.address:08X}')
 rec={'entry':e,'row':r,'direct':ds,'exact':es,'slots':slots,'sha':sha,'fw':fw[:12],'pc':pc[:12],'body_n':len(body)}
 if ds or es: C1.append(rec); PASS.add(e)
 elif slots and any(VTREF.get(b) for b,k in slots): C2.append(rec)
print('STAGE static',len(TARGETS),flush=True)
print('STATIC',len(TARGETS),'PASS/C1',len(C1),'direct',sum(1 for x in C1 if x['direct']),'exact-only',sum(1 for x in C1 if not x['direct'] and x['exact']),'C2',len(C2))
print('TABLES',len(TABLES),'WRITES',len(WRITE),'VTREF tables',len(VTREF),'EXACT targets',len(EXACT))
rng=random.Random(20261118); sample=rng.sample(sorted(TARGETS),40); mis=[e for e in sample if e in PASS]
print('BASELINE seed20261118 sample40 mis',len(mis))
# write evidence
with open(EV+'/direct_call_sites.tsv','w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t'); w.writerow(['entry','site','caller','bytes','insn'])
 for e,r2 in sorted(TARGETS.items()):
  for s in DIRECT.get(e,[]):
   i=next((x for x in REAL if x.address==s),None); ow=owner_of(s)
   w.writerow([f'{e:08X}',f'{s:08X}',f'{int(ow["entry"],16):08X}' if ow else '',i.bytes.hex().upper() if i else '',f'{i.mnemonic} {i.op_str}' if i else ''])
with open(EV+'/exact_dispatch_sites.tsv','w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t'); w.writerow(['entry','site','caller','global','slot','vt','write_src','write_site','insn'])
 for e,r2 in sorted(TARGETS.items()):
  for site,g,k,vt,src,ws,insn in EXACT.get(e,[]):
   ow=owner_of(site); w.writerow([f'{e:08X}',f'{site:08X}',f'{int(ow["entry"],16):08X}' if ow else '',f'{g:08X}',k,f'{vt:08X}',src,f'{ws:08X}',insn])
with open(EV+'/unselected_c1_pass.tsv','w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t'); w.writerow(['entry','n_direct','n_exact'])
 for x in C1[40:]: w.writerow([f'{x["entry"]:08X}',len(x['direct']),len(x['exact'])])
json.dump({'static':len(TARGETS),'c1_pass':len(C1),'c1_selected':min(40,len(C1)),'c2':len(C2),'baseline_sample':40,'baseline_mis':len(mis),'baseline_seed':20261118,'direct_rows':sum(1 for x in C1 if x['direct']),'exact_only_rows':sum(1 for x in C1 if not x['direct'] and x['exact'])},open(EV+'/core_numbers.json','w',encoding='utf-8'),indent=2)
json.dump({'selected':[{'entry':f'{x["entry"]:08X}','ring':'DIRECT' if x['direct'] else 'EXACT','direct':[f'{s:08X}' for s in x['direct'][:8]],'exact':[f'{q[0]:08X}' for q in x['exact'][:8]],'slots':[f'{b:08X}s{k}' for b,k in x['slots'][:8]],'sha':x['sha'],'fw':x['fw'],'pc':x['pc'],'body_n':x['body_n']} for x in C1[:40]],'c2':[{'entry':f'{x["entry"]:08X}','slots':[f'{b:08X}s{k}' for b,k in x['slots'][:4]],'sha':x['sha'],'fw':x['fw'],'pc':x['pc'],'body_n':x['body_n']} for x in C2]},open(EV+'/classification.json','w',encoding='utf-8'),indent=2)
print('wrote evidence')