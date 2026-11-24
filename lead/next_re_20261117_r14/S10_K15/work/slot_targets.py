import sys,common
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
for s in sys.argv[1:]:
 disp=int(s,0)
 print('\nSLOT',hex(disp),'idx',disp//4)
 for vt in common.vtable_info():
  if vt['class'] not in ['.?AVTechnoClass@@','.?AVFootClass@@','.?AVAircraftClass@@','.?AVBuildingClass@@','.?AVUnitClass@@']: continue
  t=common.u32(vt['vt']+disp)
  cr=cov.get(f'{t:08X}') if t else None
  print(vt['class'],hex(vt['vt']),hex(t) if t else None,(cr[1],cr[2],cr[4]) if cr else None)
