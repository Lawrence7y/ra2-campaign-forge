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
vt=0x7EDCC0
out=[]
out.append(f'vtable {vt:08X} COL={R.u32(vt-4):08X} RTTI={R.rtti_from_col(R.u32(vt-4))}')
for slot in range(129,157):
 va=R.u32(vt+4*slot); e=f'{va:08X}'; r=by.get(e.lower())
 b=R.read(va,6).hex()
 out.append(f'slot {slot:3d} (+0x{4*slot:03X}) -> {e} bytes6={b} cov=({r["subsystem"]},{r["grade"].strip()},{r["name"]})' if r else f'slot {slot:3d} (+0x{4*slot:03X}) -> {e} bytes6={b} cov=NOT_FOUND')
out.append('\n=== bodies for non-stub-looking slot targets ===')
for slot in range(129,157):
 va=R.u32(vt+4*slot)
 if R.read(va,6)==bytes.fromhex('b8c2010000c3'): continue
 out.append(f'\n--- slot {slot} @ {va:08X} ---')
 out.append(R.block(va,count=140,max_bytes=4096))
txt='\n'.join(out); (root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/mission_vtable_handlers.txt').write_text(txt,encoding='utf-8')
print(f'WROTE {len(txt)} bytes')
print('\n'.join(out[:120]))
