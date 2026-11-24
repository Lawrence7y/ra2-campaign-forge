import os,csv,hashlib,struct,collections,random,json,re
import capstone,pefile
ROOT='D:/Project/ra2-campaign-forge'; OUT=ROOT+'/lead/next_re_20261117_r14/S10_KPROVED'
WORK=OUT+'/work'; EV=OUT+'/EVIDENCE'; os.makedirs(WORK,exist_ok=True); os.makedirs(EV,exist_ok=True)
EXE=ROOT+'/ra2youli/gamemd.exe'; B=open(EXE,'rb').read()
PE=pefile.PE(EXE,fast_load=True); BASE=PE.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in PE.sections:
 nm=s.Name.rstrip(b'\x00').decode(errors='replace'); va=BASE+s.VirtualAddress; SECS.append((nm,va,va+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize))
def rd(va,n):
 for nm,a,z,raw,sz,vs in SECS:
  if a<=va<z:
   o=raw+(va-a)
   return B[o:o+n] if 0<=o and o+n<=len(B) else None
 return None
def u32(va):
 x=rd(va,4); return struct.unpack('<I',x)[0] if x and len(x)==4 else None
TSEC=[s for s in SECS if s[0]=='.text'][0]; _,TLO,THI,TRAW,TSZ,TVS=TSEC
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
def disasm_range(lo,size): return list(MD.disasm(B[TRAW+(lo-TLO):TRAW+(lo-TLO)+size],lo))
# selfcheck
sc=[]
for hx in ['E800000000','FF92A4000000','FF548108']:
 i=next(MD.disasm(bytes.fromhex(hx),0x1000)); sc.append({'bytes':hx,'insn':i.mnemonic+' '+i.op_str,'op_types':[o.type for o in i.operands],'mem_index':[getattr(o,'mem',None).index if o.type==capstone.x86.X86_OP_MEM else None for o in i.operands],'has_op_index_attr':[hasattr(o,'index') for o in i.operands]})
json.dump(sc,open(EV+'/capstone_selfcheck.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
# coverage/atlas
COVCOLS=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
with open(ROOT+'/lead/next_re_20261117_r14/COVERAGE/coverage.tsv','r',encoding='utf-8',newline='') as f:
 f.readline(); COV=[dict(zip(COVCOLS,l.rstrip('\r\n').split('\t'))) for l in f if l.strip()]
with open(ROOT+'/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv','r',encoding='utf-8',newline='') as f:
 ah=f.readline().strip().split('\t'); AT={r['entry'].upper():dict(zip(ah,r.rstrip('\r\n').split('\t'))) for r in []}
 ATL=[]
with open(ROOT+'/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv','r',encoding='utf-8',newline='') as f:
 ah=f.readline().strip().split('\t'); ATL=[dict(zip(ah,l.rstrip('\r\n').split('\t'))) for l in f if l.strip()]
AT={r['entry'].upper():r for r in ATL}
S10=[r for r in COV if r['subsystem'].strip().upper()=='S10' and r['entry'].upper() in AT]
STATIC=[r for r in S10 if r['grade']=='[静态推断]']
TARGETS={int(r['entry'],16):r for r in STATIC}
ALLINS=disasm_range(TLO,TVS)
OWNER={}
for r in ATL:
 try: e=int(r['entry'],16); sz=int(r['size'])
 except: continue
 if TLO<=e<TLO+TVS:
  OWNER[e]=(min(TLO+TVS,e+sz),r)
def owner_of(va):
 if va not in OWNER: return None
 return OWNER[va][1]
# vtables in rdata/data: tend to start after a COL pointer at vt-4; enumerate any aligned va whose slots include target and with RTTI-readable vt-4
VT_SLOTS=collections.defaultdict(list)
for va in range(0x7e1000,0x811074-4,4):
 col=u32(va-4)
 if not col or not (0x7e1000<=col<0x811074): continue
 td=u32(col+0xC)
 if not td or not (0x7e1000<td<0x811074): continue
 nm=rd(td+8,48)
 if not nm: continue
 z=nm.find(b'\x00'); name=nm[:z if z>=0 else len(nm)].decode('ascii',errors='ignore')
 if not name.startswith('.?A'): continue
 for k in range(0,400):
  v=u32(va+4*k)
  if v in TARGETS: VT_SLOTS[v].append((va,k,col,td,name))
# parse xrefs to vt in instruction immediates
VTREF=collections.defaultdict(list); IMMREF=collections.defaultdict(list); DIRECT=collections.defaultdict(list)
print('DEBUG target count',len(TARGETS))
for i in ALLINS:
 if i.id==0: continue
 if i.mnemonic=='data' or not i.operands: continue
 for o in i.operands:
  if o.type==capstone.x86.X86_OP_IMM:
   IMMREF[o.imm].append(i.address)
   if o.imm in VT_SLOTS: VTREF[o.imm].append(i.address)
 if i.mnemonic=='call' and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM and i.operands[0].imm in TARGETS:
  DIRECT[i.operands[0].imm].append(i.address)
# global vptr writes: C7 05 <glob> <vt>; plus constructor-style mov reg,glob then mov [reg+off],vt
WRITE=collections.defaultdict(list)
for i in ALLINS:
 if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM and i.operands[0].mem.base==0 and i.operands[1].type==capstone.x86.X86_OP_IMM:
  g=i.operands[0].mem.disp; v=i.operands[1].imm
  if v in VT_SLOTS: WRITE[(g,0,v)].append(('ABS',i.address))
regmap={}
for idx,i in enumerate(ALLINS):
 if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_REG and i.operands[1].type==capstone.x86.X86_OP_IMM and 0x812000<=i.operands[1].imm<0xb79be4:
  regmap[(idx,i.operands[0].reg)]=i.operands[1].imm
for idx,i in enumerate(ALLINS):
 if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM and i.operands[1].type==capstone.x86.X86_OP_IMM:
  v=i.operands[1].imm
  if v not in VT_SLOTS: continue
  off=i.operands[0].mem.disp; base=i.operands[0].mem.base
  for j in range(max(0,idx-80),idx):
   p=ALLINS[j]
   if p.mnemonic=='mov' and len(p.operands)==2 and p.operands[0].reg==base and p.operands[1].type==capstone.x86.X86_OP_IMM:
    g=p.operands[1].imm
    if 0x812000<=g<0xb79be4: WRITE[(g,off,v)].append(('CTOR',p.address))
    break
# exact dispatch scan: global loaded to reg vptr, call [reg+off], target matches vt slot; require writable global evidence
EXACT=collections.defaultdict(list)
for idx,i in enumerate(ALLINS):
 if i.id==0 or i.mnemonic=='data' or not i.operands: continue
 if i.mnemonic!='call' or not i.operands or i.operands[0].type!=capstone.x86.X86_OP_MEM: continue
 op=i.operands[0].mem
 if op.base==0 or op.index!=0 or op.disp%4: continue
 slots=[(j,ALLINS[j]) for j in range(max(0,idx-5),idx)]
 # reg = [global] pattern
 for j,p in reversed(slots):
  if p.mnemonic!='mov' or len(p.operands)!=2: continue
  if p.operands[0].type!=capstone.x86.X86_OP_REG or p.operands[0].reg!=op.base: continue
  if p.operands[1].type!=capstone.x86.X86_OP_MEM or p.operands[1].mem.base!=0: continue
  g=p.operands[1].mem.disp; break
 else: continue
 for (wg,wo,vt),srcs in WRITE.items():
  if wg!=g or wo!=0: continue
  t=u32(vt+op.disp)
  if t in TARGETS: EXACT[t].append((i.address,g,op.disp//4,vt,srcs[0][0],srcs[0][1],i.mnemonic+' '+i.op_str))
print('DEBUG direct rows',len(DIRECT),'exact rows',len(EXACT),'vt rows',len(VT_SLOTS),'writes',len(WRITE))
# direct/exact pass; external site owner must not be target itself
C1=[]; C2=[]
for e,r in sorted(TARGETS.items()):
 ds=[s for s in DIRECT.get(e,[]) if owner_of(s) is not None and int(owner_of(s)['entry'],16)!=e]
 es=[x for x in EXACT.get(e,[]) if owner_of(x[0]) is not None and int(owner_of(x[0])['entry'],16)!=e]
 sl=VT_SLOTS.get(e,[]); body_end=OWNER.get(e,(0,None))[0]
 body=disasm_range(e,max(0,body_end-e)) if body_end else []
 sha=hashlib.sha256(('|'.join(f'{x.mnemonic} {x.op_str}' for x in body)).encode()).hexdigest()[:12].upper()
 fw=[]; pc=[]
 for x in body:
  if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[0].type==capstone.x86.X86_OP_MEM and x.operands[0].mem.base!=0:
   fw.append(f'{x.op_str.split('[')[1].split(' ')[0]}+0x{x.operands[0].mem.disp:x}=0x{x.operands[1].imm:x}')
  if x.mnemonic=='call' and x.operands and x.operands[0].type==capstone.x86.X86_OP_IMM and x.operands[0].imm in COV and any(c['entry']==f'{x.operands[0].imm:08X}' and c['grade']=='[已证]' for c in COV): pc.append(f'{x.operands[0].imm:08X}@{x.address:08X}')
 if ds or es:
  C1.append({'entry':e,'row':r,'direct':ds,'exact':es,'slots':sl,'sha':sha,'fw':fw[:10],'pc':pc[:10],'body_n':len(body)})
 elif sl and VTREF.get(sl[0][0]): C2.append({'entry':e,'row':r,'slots':sl,'sha':sha,'fw':fw[:10],'pc':pc[:10],'body_n':len(body)})
print('C1',len(C1),'C2',len(C2),'direct rows',sum(1 for x in C1 if x['direct']),'exact rows',sum(1 for x in C1 if not x['direct'] and x['exact']))
# baseline: random 40 static rows using our full C1 predicate (direct/exact pass)
allpass=[e for e in TARGETS if (any(owner_of(s) and int(owner_of(s)['entry'],16)!=e for s in DIRECT.get(e,[])) or any(owner_of(x[0]) and int(owner_of(x[0])['entry'],16)!=e for x in EXACT.get(e,[])))]
rng=random.Random(20261118); sample=rng.sample(sorted(TARGETS),min(40,len(TARGETS))); mis=[e for e in sample if e in set(allpass)]
print('pass pool',len(allpass),'baseline mis',len(mis),'sample',len(sample))
# write machine evidence
with open(EV+'/direct_call_sites.tsv','w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t'); w.writerow(['entry','site','caller','bytes','insn'])
 for e in sorted(TARGETS):
  for s in DIRECT.get(e,[]):
   ins=next((x for x in ALLINS if x.address==s),None); ow=owner_of(s)
   w.writerow([f'{e:08X}',f'{s:08X}',f'{int(ow["entry"],16):08X}' if ow else '',ins.bytes.hex().upper() if ins else '',f'{ins.mnemonic} {ins.op_str}' if ins else ''])
with open(EV+'/exact_dispatch_sites.tsv','w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t'); w.writerow(['entry','site','caller','global','slot','vt','write_src','write_site','insn'])
 for e in sorted(TARGETS):
  for site,g,k,vt,src,ws,insn in EXACT.get(e,[]):
   ow=owner_of(site); w.writerow([f'{e:08X}',f'{site:08X}',f'{int(ow["entry"],16):08X}' if ow else '',f'{g:08X}',k,f'{vt:08X}',src,f'{ws:08X}',insn])
json.dump({'c1':len(C1),'c2':len(C2),'pass_pool':len(allpass),'baseline_mis':len(mis),'baseline_sample_size':len(sample),'selected':[f'{x["entry"]:08X}' for x in C1]},open(EV+'/core_numbers.json','w',encoding='utf-8'),indent=2)
print('wrote machine evidence')