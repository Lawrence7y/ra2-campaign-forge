import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *
for vt in (0x007E7F7C, 0x007E8344, 0x007ECE34):
    print('vt %s slot0 bytes=%s' % (hx(vt), read_va(vt,4).hex().upper()))
print('slot 007E835C bytes=', read_va(0x007E835C,4).hex().upper(), ' val=', hx(u32(0x007E835C)))
for a in (0x006C403C,0x006C493C,0x006C41C0):
    for i in dis(a-6, read_va(a-6,14)):
        print('  %s %-12s %s' % (hx(i.address), i.bytes.hex().upper(), i.mnemonic+' '+i.op_str))
    print('  ---')
print('TD of Jumpjet main:', hx(u32(u32(0x007ECE34-4)+0xC)))
print('COL Drive main:', hx(u32(0x007E7F7C-4)), ' COL DropPod main:', hx(u32(0x007E8344-4)), ' COL Jumpjet main:', hx(u32(0x007ECE34-4)))
