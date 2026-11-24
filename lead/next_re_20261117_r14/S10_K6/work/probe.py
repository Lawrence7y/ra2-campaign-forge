#!/usr/bin/env python3
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\work')
import re_lib as R
for s in ['005B2DA0','005B3060','005B34E8','005B3740','005B3970','005B3A10','005B3A60','005B3A70','005B3A80','005B3A90','005B3AA0','005B3AB0','005B3AC0','005B3AD0','005B3AE0']:
 va=int(s,16); print('\n===== '+s+' '+R.section_of(va)+' ====='); print(R.block(va,count=220,max_bytes=4000))
print('\n===== mission name table =====')
for i in range(32):
 p=0x816CAC+i*4; q=R.u32(p); print(f'{i:2d} {p:08X} -> {q:08X} {R.cstr(q,80)!r}')
