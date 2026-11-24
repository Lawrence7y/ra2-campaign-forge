from __future__ import annotations
import os,sys,re,struct,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_K6'
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
raw=open(ATL,'r',encoding='utf-8-sig').read().splitlines(); hdr=raw[0].split('\t')
atlas=[]; ints=[]; meta={}
for ln in raw[1:]:
 p=ln.split('\t'); p += ['']*(len(hdr)-len(p)); d=dict(zip(hdr,p))
 try:a=int(d['entry'],16); sz=int(d.get('size','0'))
 except:continue
 b=a+sz; atlas.append((a,b)); ints.append((a,b)); meta[a]=d
ints.sort()
craw=open(COV,'r',encoding='utf-8-sig').read().splitlines(); ch=craw[0].split(',')
cov={}
for ln in craw[1:]:
 p=ln.split('\t'); p+=['']*(len(ch)-len(p)); d=dict(zip(ch,p)); cov[d['entry'].strip().lower()]=d
def owner(va):
 for a,b in ints:
  if a<=va<b:return a,b
 return None
def cdesc(va):
 o=owner(va)
 if not o:return ''
 d=cov.get(f'{o[0]:08x}')
 return f"{o[0]:08X}:{d.get('subsystem','')}:{d.get('grade','')}:{d.get('name','')}" if d else f'{o[0]:08X}'
def rtti_from_col(col):
 if not col:return None
 td=pu.u32(col+0xC)
 if not td:return None
 b=pu.read(td+8,200) or b''
 s=b.split(b'\0')[0]
 try:n=s.decode('ascii')
 except:return None
 return (col,td,n) if n.startswith('.?AV') and n.endswith('@@') else None
def vtable_context(ref):
 # scan backwards/forwards for contiguous members; find any COL immediately before candidate starts
 out=[]
 for back in range(0,0x400,4):
  st=ref-back
  col=pu.u32(st-4) if st>=4 else None
  rr=rtti_from_col(col)
  if not rr:continue
  # count consecutive code VA dwords from st until not in atlas
  members=[]
  for k in range(0,256):
   v=pu.u32(st+4*k)
   if v is None or owner(v) is None:break
   members.append((st+4*k,v))
  if members and any(a==ref for a,v in members):
   out.append((st,rr[2],rr[0],rr[1],members))
  if len(out)>=5:break
 return out
def strat(va):
 for n,vb,vs,pr,rs,ch in pu.sections():
  if vb<=va<vb+min(vs,rs):
   b=pu.read(va,200); s=(b or b'').split(b'\0')[0]
   if len(s)>=3 and all(32<=c<127 for c in s):return s.decode('ascii')
 return None
TARGETS=[0x40E340,0x427940,0x42E410,0x433CF0,0x4355B0,0x43AE50]
imports={}
for ent in pu._pe.DIRECTORY_ENTRY_IMPORT:
 dll=ent.dll.decode('latin1') if isinstance(ent.dll,bytes) else ent.dll
 for imp in ent.imports:
  if imp.address:imports[imp.address]=dll+'!'+(imp.name.decode('latin1') if imp.name else 'ord:'+str(imp.ordinal))
lines=[]
lines.append('S17-K6 independent target recon')
lines.append('time='+datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'))
for t in TARGETS:
 lines.append('\n===== 0x%X ====='%t)
 d=meta.get(t,{}); lines.append('atlas='+repr(d))
 b=pu.read(t,int(d.get('size','128') or 128)); lines.append('bytes='+(b.hex(' ') if b else 'NONE'))
 strs=[]; vt=[]; iat=[]; calls=[]; ind=[]
 for ins in pu.disasm(t,int(d.get('size','128') or 128)):
  for op in ins.operands:
   if op.type==pu.X86_OP_IMM:
    v=op.imm&0xffffffff; s=strat(v)
    if s:strs.append((ins.address,v,s))
    if pu.u32(v-4): pass
   if op.type==pu.X86_OP_MEM and ins.mnemonic in ('call','jmp'):
    disp=op.mem.disp&0xffffffff
    if disp in imports:iat.append((ins.address,imports[disp]))
    else:ind.append((hex(ins.address),ins.mnemonic,ins.op_str))
   if ins.mnemonic in ('call','jmp') and op.type==pu.X86_OP_IMM:calls.append((ins.address,op.imm&0xffffffff))
 lines.append('str_imms='+repr(strs))
 lines.append('iat='+repr(iat))
 lines.append('direct_calls='+repr([(hex(a),hex(v),cdesc(v)) for a,v in calls]))
 lines.append('indirect='+repr(ind))
 refs=pu.scan_imm32_refs(t)
 lines.append('dword_refs_count='+str(len(refs)))
 lines.append('dword_refs_first='+repr([(hex(a),s,cdesc(t)) for a,s in refs[:30]]))
 vctx=[]
 for a,s in refs[:200]:
  for st,cls,col,td,mem in vtable_context(a)[:1]:
   idx=(a-st)//4
   vctx.append((hex(a),hex(st),cls,hex(col),hex(td),idx,len(mem)))
 lines.append('vtable_contexts='+repr(vctx[:20]))
 callers=pu.scan_rel32_calls(t)
 lines.append('direct_callers_count='+str(len(callers)))
 lines.append('direct_callers='+repr([(hex(a),cdesc(a)) for a,_ in callers[:60]]))
 lines.append('-- disasm --')
 for ins in pu.disasm(t,int(d.get('size','128') or 128)):
  ex=''
  for op in ins.operands:
   if op.type==pu.X86_OP_IMM:
    v=op.imm&0xffffffff; s=strat(v)
    if s:ex+=' ; STR '+repr(s)
    if v in imports:ex+=' ; IAT '+imports[v]
    if owner(v):ex+=' ; CODE '+cdesc(v)
   if op.type==pu.X86_OP_MEM and ins.mnemonic in ('call','jmp'):
    disp=op.mem.disp&0xffffffff
    if disp in imports:ex+=' ; IAT '+imports[disp]
  lines.append(f'0x{ins.address:X}: {ins.mnemonic:<7} {ins.op_str}{ex}')
txt='\n'.join(lines)+'\n'
open(OUT+r'\EVIDENCE\targets_recon.txt','w',encoding='utf-8').write(txt)
print(txt)
