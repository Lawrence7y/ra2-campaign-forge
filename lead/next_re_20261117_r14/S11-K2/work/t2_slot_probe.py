"""
S11-K2 T2/T4 probe: dump slot 11 and 12 of each class's off=4 main vtable (50 slots),
and slot 7/8 of off=0 interface, disassemble first bytes to find GetSize (B8 imm32 C3)
and WhatAmI (mov eax, imm; ret). Also handle 6A imm8 / other push forms later.
"""
import json
from pehelp import u32, is_code, disasm, fmt, section_of

J = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj = json.load(open(J, encoding='utf-8'))
classes = obj['classes']

# pick one canonical main vtable (off=4) per class
def pick(slots):
    for s in slots:
        if s['off']==4 and s['slots']==50 and section_of(s['vt'])=='.rdata':
            return s
    return None

print('class | main_vt | slot11 | slot12 | off0 slot7/8 | note')
for name,slots in sorted(classes.items()):
    m=pick(slots)
    if not m: 
        print(name,'NO MAIN'); continue
    vt=m['vt']
    s11=u32(vt+11*4); s12=u32(vt+12*4)
    print('\n===',name,'mainVT=%08X'%vt,'===')
    for idx in (10,11,12,13):
        a=u32(vt+idx*4)
        if is_code(a):
            ins=disasm(a,16)
            print(' slot%-2d %08X : %s' % (idx,a,' | '.join(fmt(x) for x in ins[:4])))
        else:
            print(' slot%-2d %08X : noncode' % (idx,a))
    # off=0 table slot 7/8 (IPersistStream GetSize/GetSizeMax)
    for s in slots:
        if s['off']==0:
            o0=s['vt']
            for idx in (7,8,9):
                a=u32(o0+idx*4)
                if is_code(a):
                    ins=disasm(a,12)
                    print(' off0 slot%-2d %08X : %s' % (idx,a,' | '.join(fmt(x) for x in ins[:3])))
                else:
                    print(' off0 slot%-2d %08X : noncode'%(idx,a))
            break
