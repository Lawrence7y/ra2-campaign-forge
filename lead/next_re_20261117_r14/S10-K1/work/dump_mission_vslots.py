#!/usr/bin/env python3
"""S10-K1: dump vtable slots 129..156 (offset 0x204..0x270) across class vtables."""
import struct
import pefile
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
def va2off(va):
    for n,v,vs,r,rs in secs:
        if v<=va<v+max(vs,rs): return r+(va-v)
    return None

vtables={
 'MissionClass':0x7EDCC0,
 'RadioClass':0x7F0508,
 'TechnoClass':0x7F4960,
 'FootClass':0x7E8C94,
 'InfantryClass':0x7EB058,
 'AircraftClass':0x7E22A4,
 'BuildingClass':0x7E3EBC,
 'UnitClass':0x7EF31C,
}
for name,base in vtables.items():
    o=va2off(base)
    if o is None:
        print("=== %s @ 0x%08X : NO MAP ==="%(name,base)); continue
    print("=== %s @ 0x%08X ==="%(name,base))
    col=struct.unpack_from('<I',data,o-4)[0]
    print("   COL[-4]=0x%08X"%col)
    for slot in range(129,157):
        val=struct.unpack_from('<I',data,o+4*slot)[0]
        print("   v[%3d](+0x%03X)=0x%08X"%(slot,4*slot,val))
