"""Byte-level: for each Locomotion class off4 subtable, resolve slot16 (+0x40) and slot23 (+0x5C),
check calls to UpdatePathfinding (0x4D3920) in the whole closure (depth1 of direct calls)."""
from pehelp import *
import json
atlas=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json',encoding='utf-8'))
off4={}
for v in atlas['vtables']:
    c=v['class'].replace('.?AV','').replace('@@','')
    if 'LocomotionClass' in c and 'TClassFactory' not in c and v['col_offset']==4:
        off4[c]=v['vt']
# known big Process funcs that call UpdatePathfinding
BIG={0x4B2630:'Drive',0x75AEC0:'Walk',0x6A1C80:'Ship',0x5B01C0:'Mech',0x5164D0:'Hover'}
def direct_calls(va,limit=4000):
    out=set()
    for i in disasm(va,limit):
        if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_IMM:
            out.add(i.operands[0].imm & 0xFFFFFFFF)
    return out
for c,vt in sorted(off4.items()):
    s16=u32(vt+0x40); s23=u32(vt+0x5C)
    dc=direct_calls(s16) if section_of(s16)=='.text' else set()
    hit=[BIG[b] for b in BIG if b in dc]
    print('%-26s off4=%08X slot16[+40]=%08X ->%s  slot23[+5C]=%08X'%(
        c,vt,s16,('calls BIG:'+','.join(hit)) if hit else '',s23))
