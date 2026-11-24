import sys
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
print('nvt',len(common.vtable_info()))
for vt in common.vtable_info():
 if 'FootClass' in vt['class'] or 'AircraftClass' in vt['class']:
  va=vt['vt']; hits=[k for k in range(vt['slots']) if common.u32(va+4*k)==0x70D990]
  if hits:
   col=common.u32(va-4); td=common.u32(col+12)
   print(repr(vt['class']),hex(va),hits,hex(col),hex(td),common.read(td,32).hex(),repr(common.cstr(td+8,80)))
