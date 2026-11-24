#!/usr/bin/env python3
import sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
addrs=[0x004D9F70,0x004D98C0,0x0051F2C0,0x00746B20,0x0070AA60,0x00519630,0x00737C90,0x0073CEC0,0x00518F90,0x004D85D0]
out=[]
for a in addrs:
 out.append(f'\n===== {a:08X} =====')
 out.append(R.block(a,count=300,max_bytes=8192))
 out.append('--- dword refs / vtables ---')
 for ref,best in R.find_vtable_containing(a,max_back=512): out.append(f'ref={ref:08X} best={best}')
txt='\n'.join(out);(root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/string_candidates_disasm.txt').write_text(txt,encoding='utf-8')
print('WROTE',len(txt))
