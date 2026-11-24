import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K5\work')
from re_lib import *
for a,n in [(0x5B3970,90),(0x4A1D50,100),(0x5F6250,100),(0x65AB10,140),(0x5B3A10,30),(0x5B3910,160),(0x5F5E80,160)]:
 print('\n===== 0x%08X ====='%a)
 print(fmt_block(a,count=n,stop_ret=True,max_bytes=8192))
