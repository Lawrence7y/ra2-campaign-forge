import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
# miss3 vtable bases
for vt in [0x7e5144,0x7e5170,0x7ece7c,0x7ece9c]:
    col=u32(vt-4);td=u32(col+0xC) if col else None
    b=rd(td+8,60) if td else None
    nm=b.split(b'\x00')[0].decode('ascii',errors='replace') if b else None
    print('vt',hex(vt),'COL',hex(col) if col else None,'TD',hex(td) if td else None,'name',repr(nm),'slot6',hex(u32(vt+0x18)),'slot1',hex(u32(vt+4)))
print('=== body of 0x40B880 (slot2 SetCapacity) full ===')
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(rd(0x40b880,0x40b930-0x40b880),0x40b880):print(hex(i.address),i.mnemonic,i.op_str)
print('=== body of 0x40B930 (slot4 FindItemIndex) full ===')
for i in md.disasm(rd(0x40b930,0x40b960-0x40b930),0x40b930):print(hex(i.address),i.mnemonic,i.op_str)
