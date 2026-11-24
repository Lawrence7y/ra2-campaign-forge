import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
for col in [0x800800]:
 td=R.u32(col+0xC); raw=R.read(td+8,80); z=raw.find(b'\0'); print(hex(col),hex(td),repr(raw[:z if z>=0 else 80]))
