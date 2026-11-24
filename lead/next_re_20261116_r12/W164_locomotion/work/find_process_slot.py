"""Find which vtable slots hold the Locomotion 'Process' functions (callers of UpdatePathfinding).
Search ALL vtables from canonical atlas (byte-level) for these function addresses."""
from pehelp import *
import json
atlas=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json',encoding='utf-8'))
targets={0x4B2630:'Drive?',0x75AEC0:'Walk?',0x6A1C80:'Ship?',0x5B01C0:'Mech?',0x5164D0:'Hover?',
         0x4CFD20:'Fly?',0x4DA530:'FootAI',0x4D3920:'UpdatePathfinding',0x55A910:'loco_common_5C'}
print('=== search all 1214 canonical vtables (scan 64 dwords each) for Process candidates ===')
for v in atlas['vtables']:
    vt=v['vt']; cls=v['class'].replace('.?AV','').replace('@@','')
    for i in range(64):
        try: d=u32(vt+4*i)
        except: break
        if d in targets:
            print('  %-28s off=%-3d vt=%08X slot=%d (+0x%X) -> %08X [%s]'%(
                cls,v['col_offset'],vt,i,4*i,d,targets[d]))
