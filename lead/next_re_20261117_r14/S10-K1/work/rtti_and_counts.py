#!/usr/bin/env python3
"""S10-K1 final: verify MissionClass RTTI TD chain + count distinct non-stub mission handlers."""
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
def rd(va): return struct.unpack_from('<I',data,va2off(va))[0]
def cstr(va):
    o=va2off(va); e=o
    while e<len(data) and data[e]!=0 and e-o<80: e+=1
    return data[o:e].decode('ascii',errors='replace')

# Verify COL -> TD chain for MissionClass vtable 0x7EDCC0
for vname,base in [('MissionClass',0x7EDCC0),('FootClass',0x7E8C94)]:
    col=rd(base-4)
    print("=== %s vtable 0x%X COL=0x%X ==="%(vname,base,col))
    # COL layout: COL+0=sig, +4=offset, +8=TD ptr (MSVC RTTI: type_info* is at +8? actually COL: sig@0, offset@4, TD@8)
    for cand in (col+8,):
        td=rd(cand)
        print("   COL[+8]=TD=0x%X"%td)
        o=va2off(td)
        if o is not None:
            print("   TD bytes:", ' '.join('%02X'%b for b in data[o:o+24]))
            print("   TD name:",repr(cstr(td+16) if td+16<0xB80000 else '?'))

# Count distinct non-stub mission handler impls across vtables
vtables={'MissionClass':0x7EDCC0,'RadioClass':0x7F0508,'TechnoClass':0x7F4960,
         'FootClass':0x7E8C94,'InfantryClass':0x7EB058,'AircraftClass':0x7E22A4,
         'BuildingClass':0x7E3EBC}
STUB_BASE=0x5B2E10; STUB_END=0x5B2FD0
def is_stub(a): return STUB_BASE<=a<STUB_END
allimpl={}
for name,base in vtables.items():
    for slot in range(129,157):
        a=rd(base+4*slot)
        if not is_stub(a):
            allimpl.setdefault(a,[]).append('%s.v%d'%(name,slot))
print("\n=== distinct non-stub mission handler impls: %d ==="%len(allimpl))
for a,refs in sorted(allimpl.items()):
    print("  0x%08X  %s"%(a,','.join(refs)))
