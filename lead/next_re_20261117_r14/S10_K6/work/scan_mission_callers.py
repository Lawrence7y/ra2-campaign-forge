#!/usr/bin/env python3
import csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
atl=load(root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv');cov={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv')}
def container(a):
 for r in atl:
  b=int(r['entry'],16); sz=int(r.get('size','0') or 0)
  if b<=a<b+sz: return r
 return None
s=[x for x in R.PE.sections if x.Name.decode('latin1').rstrip('\0')=='.text'][0]
base=R.IB+s.VirtualAddress; data=R.read(base,s.SizeOfRawData)
ins=[i for i in R.MD.disasm(data,base) if i.id!=0]
keys={0x5B3570:'QueueMission?',0x5B35E0:'?122',0x5B3650:'?125',0x5B36B0:'?126',0x5B3060:'Update',0x5B3A10:'HasPending'}
out=[]
for idx,i in enumerate(ins):
 if i.mnemonic!='call' or not i.operands or i.operands[0].type!=R.X86_OP_IMM: continue
 t=i.operands[0].imm
 if t not in keys: continue
 c=container(i.address)
 if not c: continue
 cr=cov.get(c['entry'].strip().lower())
 if not cr or cr['subsystem'].strip().upper()!='S10' or cr['grade'].strip()=='[已证]': continue
 out.append(f'\n=== site {i.address:08X} target {t:08X} {keys[t]} in {c["entry"]} name={cr["name"]} grade={cr["grade"].strip()} size={c["size"]} ===')
 for j in ins[max(0,idx-14):idx+6]: out.append(R.fmt(j))
# generic virtual calls to queue-mission slot123 (disp 0x1EC) with surrounding context
for idx,i in enumerate(ins):
 if i.mnemonic not in ('call','jmp') or not i.operands or i.operands[0].type!=R.X86_OP_MEM: continue
 if i.operands[0].mem.disp!=0x1EC: continue
 c=container(i.address)
 if not c: continue
 cr=cov.get(c['entry'].strip().lower())
 if not cr or cr['subsystem'].strip().upper()!='S10' or cr['grade'].strip()=='[已证]': continue
 out.append(f'\n=== VSLOT123 site {i.address:08X} in {c["entry"]} name={cr["name"]} grade={cr["grade"].strip()} ===')
 for j in ins[max(0,idx-14):idx+6]: out.append(R.fmt(j))
txt='\n'.join(out);(root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/mission_callee_caller_scan.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt),'blocks',sum(1 for x in out if x.startswith('\n===')))
