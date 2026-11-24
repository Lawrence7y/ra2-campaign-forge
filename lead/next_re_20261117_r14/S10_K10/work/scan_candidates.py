from pathlib import Path
import csv,re,struct,collections
from capstone import *
from capstone.x86 import *
try:
 from capstone.x86 import reg_name
except Exception:
 reg_name=lambda r: str(r)
import pefile
R=Path(r'D:\Project\ra2-campaign-forge')
COV=R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=R/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=R/'ra2youli/gamemd.exe'
def load():
 with COV.open(encoding='utf-8',newline='') as f: cov=list(csv.DictReader(f,delimiter='\t'))
 with ATL.open(encoding='utf-8',newline='') as f: atl={r['entry'].strip().lower():r for r in csv.DictReader(f,delimiter='\t')}
 pe=pefile.PE(str(EXE)); data=EXE.read_bytes()
 image=pe.OPTIONAL_HEADER.ImageBase
 def off(va):
  r=va-image
  for s in pe.sections:
   if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
    o=s.PointerToRawData+r-s.VirtualAddress
    if o<len(data): return o
  return None
 def string_at(va):
  o=off(va)
  if o is None:return ''
  raw=data[o:o+160]; z=raw.find(b'\0')
  if z<3:return ''
  s=raw[:z]
  if len(s)>100 or any(c<32 or c>126 for c in s):return ''
  return s.decode('ascii','replace')
 md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
 names={r['entry'].strip().lower():r for r in cov}
 def dis(entry,size=None,maxb=4096):
  e=entry.strip().lower(); va=int(e,16)
  if size is None: size=int(atl[e]['size']) if e in atl else maxb
  o=off(va)
  if o is None:return []
  code=data[o:o+min(int(size),maxb)]
  return list(md.disasm(code,va))
 return cov,atl,names,pe,data,image,off,string_at,md,dis
def feats(insns,off,string_at,names):
 out={'calls':[],'vcalls':[],'writes':[],'consts':[],'strings':[],'tail':''}
 for m in insns:
  if m.id==0: continue
  s=m.op_str.strip()
  if m.mnemonic=='call' and m.operands:
   op=m.operands[0]
   if op.type==X86_OP_IMM:
    va=op.imm&0xffffffff; key=f'{va:08X}'
    nm=names.get(key.lower(),{}).get('name','')
    gr=names.get(key.lower(),{}).get('grade','')
    out['calls'].append((key,nm,gr))
   elif op.type==X86_OP_MEM: out['vcalls'].append(s)
  if m.mnemonic in ('mov','movzx','movsx','and','or','xor','add','sub','inc','dec') and m.operands and m.operands[0].type==X86_OP_MEM:
   mem=m.operands[0].mem
   if mem.base in (X86_REG_ECX,X86_REG_ESI,X86_REG_EDI,X86_REG_EBX,X86_REG_EAX,X86_REG_EDX):
    disp=mem.disp
    if 0<disp<0x2000: out['writes'].append((m.mnemonic,reg_name(mem.base),disp,s))
  for op in m.operands:
   if op.type==X86_OP_IMM:
    v=op.imm&0xffffffff
    if v<=0xffff: out['consts'].append(v)
   if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.disp:
    st=string_at(op.mem.disp&0xffffffff)
    if st: out['strings'].append(st)
   if op.type==X86_OP_IMM:
    st=string_at(op.imm&0xffffffff)
    if st: out['strings'].append(st)
  if m.mnemonic in ('ret','retf'): out['tail']=m.mnemonic+' '+m.op_str
 return out
if __name__=='__main__':
 cov,atl,names,pe,data,image,off,string_at,md,dis=load()
 rows=[]
 for r in cov:
  if r['subsystem']!='S10' or r['grade']=='[已证]':continue
  e=r['entry'].strip().lower()
  if e not in atl:continue
  ins=dis(e)
  f=feats(ins,off,string_at,names)
  known=[c for c in f['calls'] if c[1] and not c[1].startswith('sub_')]
  writes={(w[1],w[2]) for w in f['writes']}
  score=len(known)*4+len(writes)+len(f['vcalls'])*2+len(f['strings'])*5+len(set(f['consts']))/10
  rows.append((score,r['entry'],r['grade'],r['name'],atl[e]['size'],len(ins),len(known),len(writes),len(f['vcalls']),';'.join(x[1] for x in known[:6]),';'.join(f['strings'][:4]),';'.join(f'{w[1]}+0x{w[2]:X}' for w in f['writes'][:8])))
 rows.sort(reverse=True)
 out=R/'lead/next_re_20261117_r14/S10_K10/EVIDENCE/CANDIDATE_SCAN.tsv'
 with out.open('w',encoding='utf-8',newline='') as f:
  w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['score','entry','grade','cov_name','size','nins','known_calls','writes','vcalls','known_callees','strings',' writes']);w.writerows(rows)
 print('rows',len(rows),'out',out)
 for x in rows[:120]: print('\t'.join(map(str,x[:10])))
