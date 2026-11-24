#!/usr/bin/env python3
import csv,sys
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\work')
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
cov=[]
with (root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv').open('r',encoding='utf-8',newline='') as f:
 for r in csv.DictReader(f,delimiter='\t'): cov.append(r)
by={r['entry'].strip().lower():r for r in cov}
vts=[0x007E22A4,0x007E3EBC,0x007E8C94,0x007EB058,0x007EDCC0,0x007F0508,0x007F4960,0x007F5C70]
stub={R.u32(0x7EDCC0+4*i) for i in range(129,157)}
out=[]
for v in vts:
 rtti=R.rtti_from_col(R.u32(v-4))
 out.append(f'\n=== {v:08X} {rtti[1] if rtti else "?"} ===')
 for slot in range(129,157):
  f=R.u32(v+4*slot); e=f'{f:08X}'; row=by.get(e.lower())
  mark='STUB' if f in stub else 'REAL'
  desc=f'{row["subsystem"]}:{row["grade"].strip()}:{row["name"]}' if row else 'NOT_COVERED'
  out.append(f'{slot:3d} {mark} {e} cov={desc}')
out.append('\n=== REAL TARGETS in S10 (non-stub) ===')
seen=set()
for v in vts:
 for slot in range(129,157):
  f=R.u32(v+4*slot)
  if f in stub or f in seen: continue
  seen.add(f); e=f'{f:08X}'; row=by.get(e.lower())
  if row and row['subsystem'].strip().upper()=='S10':
   out.append(f'\n--- {e} slot={slot} vtable={v:08X} grade={row["grade"].strip()} name={row["name"]} ---')
   out.append(R.block(f,count=140,max_bytes=4096))
txt='\n'.join(out); (root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/mission_subclass_map.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt))
