#!/usr/bin/env python3
import sys,csv,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
cov=load(root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'); atl={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv')}; by={r['entry'].strip().lower():r for r in cov}
def sect(va):
 for s in R.PE.sections:
  b=R.IB+s.VirtualAddress
  if b<=va<b+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.Name.decode('latin1').rstrip('\0')
 return '?'
def str_at(va):
 try:
  if sect(va) not in ('.rdata','.data'): return None
  b=R.read(va,80); z=b.split(b'\0',1)[0]
  if 3<=len(z)<=70 and sum(32<=c<127 for c in z)>=len(z)*0.9: return z.decode('latin1')
 except: pass
 return None
addrs=[int(x,16) for x in sys.argv[1:]] or [0x4D9F70,0x4D98C0,0x51F2C0,0x746B20,0x70AA60]
out=[]
for a in addrs:
 e=f'{a:08X}'; row=by.get(e.lower()); ar=atl.get(e.lower()); size=int(ar.get('size','0') or 0) if ar else 400
 out.append(f'\n===== {e} row={row} atlas_size={size} =====')
 out.append('--- vtables ---')
 for ref,best in R.find_vtable_containing(a,max_back=512): out.append(f'ref={ref:08X} best={best}')
 ins=list(R.MD.disasm(R.read(a,min(size or 512,5000)),a))
 out.append('--- immediate strings ---')
 for i in ins:
  if i.id==0: continue
  for op in i.operands:
   if op.type==R.X86_OP_IMM:
    s=str_at(op.imm)
    if s: out.append(f'{i.address:08X} imm={op.imm:08X} {s!r}')
    try:
     q=R.u32(op.imm); s2=str_at(q)
     if s2: out.append(f'{i.address:08X} ptr={op.imm:08X}->{q:08X} {s2!r}')
    except: pass
 out.append('--- direct calls ---')
 for i in ins:
  if i.id==0 or i.mnemonic!='call' or not i.operands: continue
  op=i.operands[0]
  if op.type==R.X86_OP_IMM:
   t=f'{op.imm:08X}'; rr=by.get(t.lower())
   out.append(f'{i.address:08X} call {t} grade={rr["grade"].strip() if rr else "?"} name={rr["name"] if rr else "?"}')
 out.append('--- disassembly ---')
 for i in ins:
  if i.id==0: out.append(f'{i.address:08X} {i.bytes.hex(" ")} .byte')
  else: out.append(R.fmt(i))
txt='\n'.join(out);(root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/candidate_details.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt))
