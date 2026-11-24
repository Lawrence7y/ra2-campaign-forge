"""Resolve AI slot [+0x5C] (slot 23) in main vtables of Object/Foot/Techno/Unit/Inf/Aircraft/Building/Bullet.
Also dump LocomotionClass offset=4 subtable method addresses (slot 23 = +0x5C) for each subclass.
Byte-level channel, no atlas dependency."""
from pehelp import *
import json

# Known main vtables (col_offset==0) from canonical atlas, verified earlier
MAIN_VT = {
 'ObjectClass':0x7E4884, # TBD from atlas
}
atlas=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json',encoding='utf-8'))
# find main vt for classes of interest
want=['ObjectClass','FootClass','TechnoClass','UnitClass','InfantryClass','AircraftClass','BuildingClass','BulletClass']
byname={}
for v in atlas['vtables']:
    byname.setdefault(v['class'].replace('.?AV','').replace('@@',''),[]).append(v)

print('=== AI slot [+0x5C]=slot23 in main vtable ===')
for c in want:
    vs=[v for v in byname.get(c,[]) if v['col_offset']==0]
    if not vs:
        # Some classes are named e.g. UnitClass@@ exactly
        continue
    v=vs[0]
    vt=v['vt']
    ai=u32(vt+0x5C)
    what=u32(vt+0x2C)
    print('%-16s vt=%08X  AI[5C]=%08X  WhatAmI[2C]=%08X' % (c, vt, ai, what))

print()
print('=== Locomotion offset=4 subtables: slot23 [+0x5C] and neighbor methods ===')
LOCO_OFF4 = {
 'LocomotionClass':0x7EADF4,'DriveLocomotionClass':0x7E7EB0,'WalkLocomotionClass':0x7F69F8,
 'HoverLocomotionClass':0x7EACFC,'FlyLocomotionClass':0x7E89F4,'JumpjetLocomotionClass':0x7ECD68,
 'TeleportLocomotionClass':0x7F5000,'ShipLocomotionClass':0x7F2D8C,
 'MechLocomotionClass':0x7EDB6C,'RocketLocomotionClass':0x7F0B1C,'TunnelLocomotionClass':0x7F5A24,
 'DropPodLocomotionClass':0x7E8278,
}
for c,vt in sorted(LOCO_OFF4.items()):
    vals=[u32(vt+4*i) for i in range(50)]
    s23=vals[23]
    print('%-26s off4 vt=%08X slot23[+5C]=%08X' % (c,vt,s23))
    # print slots 20..26 for context
    print('     slot20..26:', ' '.join('%02d:%08X'%(i,vals[i]) for i in range(20,27)))

print()
print('=== Locomotion MAIN tables (offset=0): all 10-12 slots ===')
LOCO_MAIN = {
 'LocomotionClass':0x7EAEC0,'DriveLocomotionClass':0x7E7F7C,'WalkLocomotionClass':0x7F6AC4,
 'HoverLocomotionClass':0x7EADC8,'FlyLocomotionClass':0x7E8AC0,'JumpjetLocomotionClass':0x7ECE34,
 'TeleportLocomotionClass':0x7F50CC,'ShipLocomotionClass':0x7F2E58,
 'MechLocomotionClass':0x7EDC38,'RocketLocomotionClass':0x7F0BE8,'TunnelLocomotionClass':0x7F5AF0,
 'DropPodLocomotionClass':0x7E8344,
}
for c,vt in sorted(LOCO_MAIN.items()):
    n=12 if c=='TeleportLocomotionClass' else 10
    vals=[u32(vt+4*i) for i in range(n)]
    print('%-26s main vt=%08X: %s' % (c,vt,' '.join('%02d:%08X'%(i,vals[i]) for i in range(n))))
