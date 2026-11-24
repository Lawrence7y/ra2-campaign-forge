#!/usr/bin/env python3
import sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
cov={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv')}; atl={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv')}
addrs=[int(x,16) for x in sys.argv[1:]]
out=[]
for a in addrs:
 e=f'{a:08X}'; row=cov.get(e.lower()); ar=atl.get(e.lower()); size=int(ar.get('size','0') or 400) if ar else 400
 out.append(f'\n===== {e} row={row} atlas_size={size} =====')
 out.append('--- RTTI/vtable anchors ---')
 for ref,best in R.find_vtable_containing(a,max_back=512): out.append(f'ref={ref:08X} best={best}')
 out.append('--- full bounded disassembly ---')
 for i in R.MD.disasm(R.read(a,min(size,6000)),a):
  if i.id==0: out.append(f'{i.address:08X} {i.bytes.hex(" ")} .byte')
  else: out.append(R.fmt(i))
txt='\n'.join(out);(root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/queue_candidate_details.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt))
