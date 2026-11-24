import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K5\work')
from re_lib import *
for a,n in [(0x4A1DE0,120),(0x4A1CA0,80),(0x410410,100),(0x410380,80),(0x6CF240,120)]:
 print('\n===== 0x%08X ====='%a)
 print(fmt_block(a,count=n,stop_ret=True,max_bytes=8192))
