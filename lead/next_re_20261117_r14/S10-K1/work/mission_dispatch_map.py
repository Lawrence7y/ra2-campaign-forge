#!/usr/bin/env python3
"""S10-K1: auto-map mission index -> name -> stub -> vtable slot -> per-class impl address."""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True

# mission names
names=['Sleep','Attack','Move','QMove','Retreat','Guard','Sticky','Enter','Capture','Eaten',
       'Harvest','Area Guard','Return','Stop','Ambush','Hunt','Unload','Sabotage','Construction',
       'Selling','Repair','Rescue','Missile','Harmless','Open','Patrol','Paradrop Approach',
       'Paradrop Overfly','Wait','Attack Move','Spyplane Approach','Spyplane Overfly']

TABLE=0x5B34E8
o=va2off(TABLE)
targets=[struct.unpack_from('<I',data,o+4*i)[0] for i in range(32)]

# parse each stub: find 'call dword ptr [reg + 0xNNN]' -> extract disp
def slot_of_stub(tva):
    oo=va2off(tva)
    for ins in md.disasm(data[oo:oo+0x40],tva):
        if ins.mnemonic=='call' and ins.op_str.startswith('dword ptr ['):
            # parse [edx + 0x204]
            import re
            m=re.search(r'\+\s*(0x[0-9a-f]+)',ins.op_str)
            if m: return int(m.group(1),16)//4
        if ins.mnemonic=='ret': break
    return None
slots=[slot_of_stub(t) for t in targets]

vtables={'MissionClass':0x7EDCC0,'RadioClass':0x7F0508,'TechnoClass':0x7F4960,
         'FootClass':0x7E8C94,'InfantryClass':0x7EB058,'AircraftClass':0x7E22A4,
         'BuildingClass':0x7E3EBC}

def vfunc(base,slot):
    oo=va2off(base)
    return struct.unpack_from('<I',data,oo+4*slot)[0]

print("idx name                  stub      slot  " + ' '.join('%-14s'%n for n in vtables))
for i in range(32):
    row="%2d  %-22s 0x%06X  v%-3s "%(i,names[i],targets[i],slots[i] if slots[i] is not None else '?')
    row+=' '.join('0x%08X'%vfunc(b,slots[i]) for b in vtables.values())
    print(row)

# disassemble base stubs 0x5B2E10..0x5B2FD0 (28 funcs, 0x10 apart)
print("\n=== base handlers 0x5B2E10..0x5B2FD0 ===")
for a in range(0x5B2E10,0x5B2FD0,0x10):
    oo=va2off(a)
    insns=[]
    for ins in md.disasm(data[oo:oo+0x10],a):
        insns.append("%s %s"%(ins.mnemonic,ins.op_str))
    print("  0x%08X: %s"%(a,' | '.join(insns)))
