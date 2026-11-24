import sys
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
print('known strings',find_imm_refs(0x46BEE0,1000)[:8])
for vt in [0x7e3d10,0x7e4948,0x7f6b30,0x7f73b8]:
 print(hex(vt),'col',hex(u32(vt-4)),'td',hex(u32(u32(vt-4)+12)),'name',cstr(u32(u32(vt-4)+12)+8,80))
print('known slot hits',vt_slots_for_entry(0x4393D0)[:10])
