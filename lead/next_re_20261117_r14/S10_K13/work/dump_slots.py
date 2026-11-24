import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
for base in [0x7EB058,0x7EB1C4-0x1c*4,0x7E8E00-0x91*4,0x7F5DFC-0x99*4,0x7E2430-0x63*4,0x7EB47C-0x105*4]:
 print('\nBASE',hex(base))
 for i in range(-3,4):
  a=base+i*4
  try:v=R.u32(a)
  except:v=None
  print(f'  {a:08X} = {v:08X}' if v is not None else f'  {a:08X} = ?')
