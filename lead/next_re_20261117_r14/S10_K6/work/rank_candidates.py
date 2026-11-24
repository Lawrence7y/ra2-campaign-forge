#!/usr/bin/env python3
"""Rank S10 non-proved functions by behavior anchors; read-only target."""
from pathlib import Path
import csv,re,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
covp=root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
atlp=root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
cov=load(covp); atl={r['entry'].strip().lower():r for r in load(atlp)}
by={r['entry'].strip().lower():r for r in cov}
def meaningful(n):
 n=n.strip()
 return bool(n) and not n.startswith('sub_') and '::sub_' not in n and re.search(r'::(?:v?slot)\d+$',n) is None
prov={e.lower():r['name'].strip() for e,r in by.items() if r['grade'].strip()=='[已证]' and meaningful(r['name'])}
# direct E8 callers from linear disassembly of .text
s=[x for x in R.PE.sections if x.Name.decode('latin1').rstrip('\0')=='.text'][0]
tbase=R.IB+s.VirtualAddress
data=R.read(tbase,s.SizeOfRawData)
callers={}
for i in R.MD.disasm(data,tbase):
 if i.id==0: continue
 if i.mnemonic=='call' and i.op_str.startswith('0x'):
  try: t=int(i.op_str,16)
  except: continue
  callers.setdefault(f'{t:08x}',[]).append(i.address)
# helpers
def section(va):
 for x in R.PE.sections:
  b=R.IB+x.VirtualAddress
  if b<=va<b+max(x.Misc_VirtualSize,x.SizeOfRawData): return x.Name.decode('latin1').rstrip('\0')
 return ''
def nice_str(va):
 try:
  if section(va) not in ('.rdata','.data'): return None
  b=R.read(va,80)
  z=b.split(b'\0',1)[0]
  if 4<=len(z)<=64 and sum(32<=c<127 for c in z)>=len(z)*0.9:
   return z.decode('latin1')
 except: pass
 return None
rows=[]
for e,r in by.items():
 if r['subsystem'].strip().upper()!='S10' or r['grade'].strip()=='[已证]' or e not in atl: continue
 va=int(e,16); size=int(atl[e].get('size','0') or 0)
 if size<=0 or size>20000: size=min(size or 512,20000)
 ins=list(R.MD.disasm(R.read(va,min(size,20000)),va))
 cal=[]; strs=[]; consts=[]; field_w=0; indirect=0
 for i in ins:
  if i.id==0: continue
  if i.mnemonic=='call' and i.operands:
   op=i.operands[0]
   if op.type==R.X86_OP_IMM and f'{op.imm:08x}' in prov: cal.append(prov[f'{op.imm:08x}'])
   elif op.type==R.X86_OP_MEM: indirect+=1
  for op in i.operands:
   if op.type==R.X86_OP_IMM and 0<=op.imm<=0xffffffff:
    st=nice_str(op.imm)
    if st: strs.append(st)
    else:
     try:
      q=R.u32(op.imm); st2=nice_str(q)
      if st2: strs.append(st2)
     except: pass
    if op.imm<=0x200: consts.append(op.imm)
  if i.mnemonic in ('mov','movzx','movsx','add','sub','and','or','xor','inc','dec','cmp','test') and len(i.operands)>=2:
   dst=i.operands[0]
   if dst.type==R.X86_OP_MEM and i.mnemonic in ('mov','movzx','movsx','add','sub','and','or','xor','inc','dec'): field_w+=1
 cal=sorted(set(cal)); strs=sorted(set(strs)); consts=sorted(set(consts))
 score=3*len(cal)+2*len(strs)+min(field_w,5)+min(len(consts),8)+(2 if callers.get(e) else 0)
 rows.append((score,e,r['grade'].strip(),r['name'],size,len(cal),len(strs),field_w,len(consts),len(callers.get(e,[])),';'.join(cal[:8]),';'.join(strs[:8]),';'.join(f'{x:X}' for x in consts[:16])))
rows.sort(reverse=True)
out=root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/ranked_candidates.tsv'
with out.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t',lineterminator='\n')
 w.writerow(['score','entry','grade','name','size','proven_callees','strings','field_ops','consts','direct_callers','callee_names','string_names','const_values'])
 for x in rows:w.writerow(x)
print('ROIES',len(rows),'WITH_PROV_CALLEE',sum(1 for x in rows if x[5]),'WITH_STR',sum(1 for x in rows if x[6]))
for x in rows[:100]: print('%4d %s %-12s sz=%-5d cal=%d str=%d fld=%d callers=%d %s | %s'%(x[0],x[1],x[3][:12],x[4],x[5],x[6],x[7],x[9],x[10][:60],x[11][:70]))
