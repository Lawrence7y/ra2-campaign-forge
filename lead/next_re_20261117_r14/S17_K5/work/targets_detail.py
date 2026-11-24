import sys,os,re,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
CARD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
# coverage: header comma, rows tab
raw=open(COV,'r',encoding='utf-8-sig').read().splitlines(); hdr=raw[0].split(',')
cov={}
for ln in raw[1:]:
 p=ln.split('\t')
 if len(p)<len(hdr): p+=['']*(len(hdr)-len(p))
 d=dict(zip(hdr,p)); cov[d['entry'].strip().lower()]=d
ints=[]; sizes={}
for ln in open(ATL,'r',encoding='utf-8-sig').read().splitlines()[1:]:
 p=ln.split('\t')
 if len(p)>=2:
  a=int(p[0],16); b=a+int(p[1]); ints.append((a,b)); sizes[a]=b-a
ints.sort()
def owner(va):
 for a,b in ints:
  if a<=va<b:return a,b
 return None
def covdesc(va):
 d=cov.get(f'{va:08x}')
 if not d: return ''
 return f"[{d.get('subsystem','')} {d.get('grade','')} {d.get('name','')}]"
def rtti(vt):
 col=pu.u32(vt-4)
 if not col: return None
 td=pu.u32(col+0xC)
 if not td: return None
 b=pu.read(td+8,160) or b''
 s=b.split(b'\0')[0]
 try: name=s.decode('ascii')
 except: return None
 if name.startswith('.?AV') and name.endswith('@@'): return (vt,col,td,name)
 return None
def str_at(va):
 if va is None: return None
 for name,vbase,vsize,praw,rawsize,ch in pu.sections():
  if vbase<=va<vbase+min(vsize,rawsize):
   b=pu.read(va,120)
   if b is None:return None
   s=b.split(b'\0')[0]
   if len(s)>=3 and all(32<=c<127 for c in s): return s.decode('ascii')
 return None
imports={}
for ent in pu._pe.DIRECTORY_ENTRY_IMPORT:
 dll=ent.dll.decode('latin1') if isinstance(ent.dll,bytes) else ent.dll
 for imp in ent.imports:
  if imp.address: imports[imp.address]=dll+'!'+(imp.name.decode('latin1') if imp.name else 'ordinal:'+str(imp.ordinal))
TARGETS=[0x4068E0,0x40E340,0x427940,0x42E410,0x433CF0,0x4355B0,0x43AE50,0x49F740,0x49F8B0,0x773450]
lines=[]
lines.append('S17-K5 target detail (independent PE/capstone/pefile sweep)')
for t in TARGETS:
 lines.append(f'\n===== TARGET 0x{t:X} =====')
 size=sizes.get(t)
 lines.append('atlas_size='+str(size))
 if size is None: size=256
 b=pu.read(t,size)
 lines.append('bytes='+(b.hex(' ') if b else 'NONE'))
 insns=pu.disasm(t,size)
 # collect refs
 strrefs=[]; vtrefs=[]; direct=[]; iats=[]; ind=[]
 for ins in insns:
  for op in ins.operands:
   if op.type==pu.X86_OP_IMM:
    val=op.imm & 0xffffffff
    s=str_at(val)
    if s: strrefs.append((ins.address,val,s))
    rr=rtti(val)
    if rr: vtrefs.append((ins.address,)+rr)
   if op.type==pu.X86_OP_MEM and ins.mnemonic in ('call','jmp'):
    d=op.mem.disp & 0xffffffff
    if d in imports: iats.append((ins.address,d,imports[d]))
    else: ind.append((ins.address,ins.mnemonic,ins.op_str))
   if ins.mnemonic in ('call','jmp') and op.type==pu.X86_OP_IMM:
    direct.append((ins.address,op.imm & 0xffffffff))
 lines.append('string_immediates='+repr(strrefs))
 lines.append('valid_rtti_vptr_writes/refs='+repr(vtrefs))
 lines.append('IAT_calls='+repr(iats))
 lines.append('direct_calls='+repr([(a,hex(d),covdesc(d)) for a,d in direct]))
 lines.append('other_indirect_call_sites='+repr([(hex(a),m,s) for a,m,s in ind[:20]])+' count='+str(len(ind)))
 refs=pu.scan_rel32_calls(t)
 lines.append('direct_callers='+repr([(hex(a),owner(a),covdesc(owner(a)[0]) if owner(a) else '') for a,_ in refs[:30]])+' count='+str(len(refs)))
 dref=pu.scan_imm32_refs(t)
 lines.append('dword_refs='+repr([(hex(a),n,owner(a),covdesc(owner(a)[0]) if owner(a) else '') for a,n in dref[:30]])+' count='+str(len(dref)))
 lines.append('-- disasm --')
 for ins in insns:
  extra=''
  for op in ins.operands:
   if op.type==pu.X86_OP_IMM:
    v=op.imm&0xffffffff
    s=str_at(v)
    if s: extra+=' ; STR '+repr(s)
    rr=rtti(v)
    if rr: extra+=' ; RTTI '+rr[3]
   if op.type==pu.X86_OP_MEM and ins.mnemonic in ('call','jmp'):
    d=op.mem.disp&0xffffffff
    if d in imports: extra+=' ; IAT '+imports[d]
   if op.type==pu.X86_OP_IMM and (v:=op.imm&0xffffffff) in cov: extra+=' ; '+covdesc(v)
  lines.append(f'0x{ins.address:X}: {ins.mnemonic:<7} {ins.op_str}{extra}')
text='\n'.join(lines)+'\n'
open(CARD+r'\EVIDENCE\targets_detail.txt','w',encoding='utf-8').write(text)
print(text[:30000])
