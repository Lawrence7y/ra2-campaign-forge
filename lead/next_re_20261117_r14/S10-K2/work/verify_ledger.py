import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\work')
from pehelp import u32
VT={'MissionClass':0x7EDCC0,'RadioClass':0x7F0508,'TechnoClass':0x7F4960,
    'FootClass':0x7E8C94,'InfantryClass':0x7EB058,'AircraftClass':0x7E22A4,
    'BuildingClass':0x7E3EBC}
STUB_LO=0x5B2E10; STUB_HI=0x5B2FD0  # S10-K1 definition
total=0; stub=0; nonstub=0; na=set()
for name,base in VT.items():
    for slot in range(129,157):
        a=u32(base+4*slot); total+=1
        if STUB_LO<=a<STUB_HI: stub+=1
        else: nonstub+=1; na.add(a)
print('S10-K1 method (RadioClass, raw range stub):')
print('  total=%d stub=%d nonstub=%d distinct-nonstub=%d'%(total,stub,nonstub,len(na)))
for a in sorted(na): print('  %08X'%a)
