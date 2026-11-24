"""Channel 2 (NO atlas dependency): full .rdata byte scan for function-address dwords.
Find every 4-byte occurrence of each Process candidate; report VA + which vtable region it falls in."""
from pehelp import *
import struct
targets={0x4B2630:'Drive_Process?',0x75AEC0:'Walk_Process?',0x6A1C80:'Ship_Process?',
         0x5B01C0:'Mech_Process?',0x5164D0:'Hover_Process?',0x4CFD20:'Fly slot23',
         0x55A910:'loco_common_slot23',0x4DA530:'FootClass::AI',0x4D3920:'UpdatePathfinding'}
# scan entire file for little-endian dwords at 4-byte alignment
import mmap
data=rd(IMAGE_BASE,0x800000) if False else None
with open(EXE,'rb') as f: blob=f.read()
# iterate on 4-byte aligned file offsets within .rdata raw range
rdata=[s for s in PE.sections if s.Name.rstrip(b'\0').decode().lower()=='.rdata'][0]
lo=rdata.PointerToRawData; hi=lo+rdata.SizeOfRawData
hits={k:[] for k in targets}
for off in range(lo,hi-3,4):
    d=struct.unpack_from('<I',blob,off)[0]
    if d in targets:
        va=IMAGE_BASE + (rdata.VirtualAddress + (off-lo))
        hits[d].append(va)
for d,name in sorted(targets.items()):
    vs=hits[d]
    print('%08X %-22s hits=%d'%(d,name,len(vs)))
    for va in vs[:20]: print('    dword@%08X'%va)
