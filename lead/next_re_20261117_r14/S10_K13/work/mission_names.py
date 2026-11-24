import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
L=[]
for i in range(32):
 p=R.u32(0x816CAC+4*i); s=R.cstring(p,80) if p else '?'; L.append(f'{i}:{s}')
print('|'.join(L))
