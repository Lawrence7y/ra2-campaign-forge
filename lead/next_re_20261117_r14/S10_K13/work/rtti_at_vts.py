import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
# exact vtable base is slot address - 4*slot; for candidates we can scan backwards up to 0x600 for a COL-looking dword and TD inline .?AV
def try_col(col):
 try:
  td=R.u32(col+0xC); raw=R.read(td+8,80); z=raw.find(b'\0'); s=raw[:z if z>=0 else 80]
  if s.startswith(b'.?AV'): return td,s.decode('latin1')
 except:pass
 return None
for slot in [0x7F5DFC,0x7E2430,0x7E8E20,0x7E8E00,0x7EB1C4,0x7EB1E4,0x7F60F0,0x7E26C8,0x7E42E0,0x7E90B8,0x7EB47C,0x7F4D84]:
 found=[]
 for back in range(0,0x601,4):
  col=try_col(slot-back)
  if col: found.append((slot-back,col))
 print(hex(slot),'COLS',[(hex(a),hex(c[0]),c[1]) for a,c in found[:5]])
