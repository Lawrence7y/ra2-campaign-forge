
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
import common
keep=['TechnoClass','FootClass','InfantryClass','UnitClass','AircraftClass','BuildingClass','ObjectClass','AbstractClass']
for vt in common.vtable_info():
 cls=vt.get('class','?').replace('.?AV','').replace('@@','')
 if cls not in keep: continue
 va=vt['vt']; col=common.u32(va-4); td=common.u32(col+0xC) if col else None; nm=common.cstr(td+8,100) if td else '?'
 print('VT',cls,hex(va),nm,'slots',vt['slots'])
 for k in range(255,272):
  p=common.u32(va+4*k)
  if p: print(' ',k,hex(4*k),f'{p:08X}')
