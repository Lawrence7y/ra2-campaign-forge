
import csv,sys,re,collections,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import re_lib as R
from capstone import *
from capstone.x86 import *
CARD=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K9')
COV=CARD/'work/s10_rows.tsv'
ATL=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
OUT=CARD/'work/s10_features.tsv'
rows=list(csv.DictReader(COV.open(encoding='utf-8'),delimiter='\t'))
atl={r['entry'].strip().lower():r for r in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t')}
proved={r['entry'].upper() for r in rows if r['grade'].strip().upper()=='[已证]'}
def str_at(x):
 try:s=R.cstring(x,120)
 except Exception:return None
 if len(s)<3:return None
 if all(32<=ord(c)<127 for c in s) and not s.startswith('?'):return s
 return None
def reg_name(i,op):
 try:return i.reg_name(op.reg)
 except Exception:return ''
feats=[]
for r in rows:
 if r['grade'].strip().upper()=='[已证]':continue
 e=r['entry'].strip().upper(); ar=atl.get(e.lower())
 if not ar:continue
 va=int(e,16); size=int(ar['size']); data=R.read(va,size)
 strings=[]; calls=[]; writes=[]; vtcalls=[]; mission_refs=0; cmps=[]
 for ins in R.MD.disasm(data,va):
  try: ops=ins.operands
  except Exception: continue
  for op in ops:
   if op.type==X86_OP_IMM:
    v=op.imm & 0xffffffff
    if ins.mnemonic=='push':
     s=str_at(v)
     if s and s not in strings:strings.append(s)
    if v==0x816CAC:mission_refs+=1
   if ins.mnemonic.startswith('call') and op.type==X86_OP_IMM:
    t=op.imm&0xffffffff;calls.append(f'{t:08X}'+('*' if f'{t:08X}' in proved else ''))
   if ins.mnemonic.startswith('call') and op.type==X86_OP_MEM and op.mem.base!=0:
    vtcalls.append(f'{reg_name(ins,op.mem.base)}+0x{op.mem.disp:x}')
   if ins.mnemonic in ('mov','movzx','movsx') and len(ins.operands)>=1 and ins.operands[0].type==X86_OP_MEM:
    op0=ins.operands[0]
    if op0.mem.base!=0 and op0.mem.disp>=0:
     writes.append(f'{reg_name(ins,op0.mem.base)}+0x{op0.mem.disp:x}')
   if ins.mnemonic=='cmp' and op.type==X86_OP_IMM and 0<=op.imm<=0x40:
    cmps.append(op.imm)
 rec={'entry':e,'grade':r['grade'],'name':r['name'],'size':size,'strings':'|'.join(strings),'nstr':len(strings),'calls':'|'.join(sorted(set(calls))),'ncall':len(set(calls)),'nprovedcall':sum(1 for c in set(calls) if c.endswith('*')),'writes':'|'.join(sorted(set(writes))),'nwrite':len(set(writes)),'vtcalls':'|'.join(sorted(set(vtcalls))),'nvcall':len(set(vtcalls)),'mission_refs':mission_refs,'cmps':'|'.join(map(str,sorted(set(cmps))))}
 feats.append(rec)
with OUT.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(feats[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(feats)
print('WROTE',OUT,'rows',len(feats))
fs=sorted(feats,key=lambda x:(-int(x['nstr']),-int(x['nprovedcall']),-int(x['nwrite']),x['entry']))
for x in fs[:80]:
 print(x['entry'],'str='+x['strings'][:100],'pcall='+str(x['nprovedcall']),'w='+str(x['nwrite']),'v='+str(x['nvcall']),'mref='+str(x['mission_refs']),x['name'][:55])
