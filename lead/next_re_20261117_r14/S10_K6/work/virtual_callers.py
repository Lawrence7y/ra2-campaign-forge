#!/usr/bin/env python3
import sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
by={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv')}
s=[x for x in R.PE.sections if x.Name.decode('latin1').rstrip('\0')=='.text'][0]
base=R.IB+s.VirtualAddress; data=R.read(base,s.SizeOfRawData)
ins=[i for i in R.MD.disasm(data,base) if i.id!=0]
targets={0x1A0:'slot104/sell',0x3B8:'slot238/lost',0x90:'slot36/tip',0x458:'slot278/text'}
out=[]
for idx,i in enumerate(ins):
 if i.mnemonic not in ('call','jmp'): continue
 if not i.operands or i.operands[0].type!=R.X86_OP_MEM: continue
 d=i.operands[0].mem.disp
 if d not in targets: continue
 out.append(f'\n=== {targets[d]} disp=0x{d:X} call@{i.address:08X} ===')
 for j in ins[max(0,idx-24):idx+5]: out.append(R.fmt(j))
for a in [0x4F9950,0x752700,0x750920,0x734E60,0x65FA70]:
 r=by.get(f'{a:08X}'.lower())
 out.append(f'\n=== callee {a:08X} coverage={r} ===')
 if a!=0x65FA70: out.append(R.block(a,count=80,max_bytes=2048))
txt='\n'.join(out);(root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/virtual_callers.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt),'hits',sum(1 for x in out if x.startswith('\n=== slot')))
