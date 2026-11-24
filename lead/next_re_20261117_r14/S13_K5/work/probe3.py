from re_core import *
for va in [0x75d0b0,0x771e70]:
    print('===',hex(va),'===')
    print('\n'.join(fmt(i) for i in dis(va,20)))
print('\nVT COL probes')
for vt in [0x7e3d10,0x7ef890,0x7f0810,0x7f6b30,0x7f73b8]:
    print(hex(vt),'vt[-4]',hex(u32(vt-4)),'td',hex(u32(vt-4)),'name',repr(cstr(u32(vt-4)+8)) if 0x7e1000<=u32(vt-4)<0x812000 else '')
