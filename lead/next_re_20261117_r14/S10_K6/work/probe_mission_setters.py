#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\work')
import re_lib as R
out=[]
for a in [0x5B3570,0x5B35E0,0x5B3650,0x5B36B0,0x410380]:
 out.append(f'\n===== {a:08X} =====\n'+R.block(a,count=180,max_bytes=8192))
(R.ROOT/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/mission_setters.txt').write_text('\n'.join(out),encoding='utf-8')
print('OK')
