#!/usr/bin/env python3
import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\work')
import re_lib as R
out=[]
for a in [0x005B35E0,0x005B3650,0x005B36B0,0x005F5E80,0x0065A970,0x0065AAA0,0x0065AB10,0x004D3590,0x005F6250,0x00410410]:
 out.append(f'\n===== {a:08X} =====')
 out.append(R.block(a,count=220,max_bytes=8192))
for a in [0x0065A970,0x0065AAA0,0x0065AB10,0x005F5E80,0x005B3570,0x005B35E0,0x005B3650,0x005B36B0]:
 out.append(f'\n===== VT refs {a:08X} =====')
 for ref,best in R.find_vtable_containing(a,max_back=256):
  out.append(f'ref={ref:08X} best={best}')
txt='\n'.join(out); (R.ROOT/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/stream_near_disasm.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt))
