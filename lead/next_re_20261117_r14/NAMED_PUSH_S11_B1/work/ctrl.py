import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *

print('== control: S22 ParasiteClass main vt 007EF890 ==')
c = rtti_of_vtable(0x007EF890)
print('  rtti=', c)
print('  slot0=', hx(u32(0x007EF890)), ' COL.offset=%#x' % u32(c['col']+4))
print('  slot bytes:', read_va(0x007EF890,8).hex())
print('  00410260 first bytes:', read_va(0x00410260,8).hex())

print()
print('== 0x7DC720 shape ==')
ins = dis(0x007DC720, read_va(0x007DC720,48))
for i in ins[:8]:
    print('   %s %-16s %s' % (hx(i.address), i.bytes.hex(), i.mnemonic+' '+i.op_str))
print()
print('== 0x7E15F4 内容 ==')
print('   dword =', hx(u32(0x007E15F4)), ' sec=', sec_name(0x007E15F4))
print('== 0x7E15F8 内容 ==')
print('   dword =', hx(u32(0x007E15F8)), ' sec=', sec_name(0x007E15F8))
print()
print('== 4 行主表 slot0 的字节（是否 thunk）==')
for vt in (0x007E7F7C, 0x007E8344, 0x007ECE34):
    s0 = u32(vt)
    print('  vt=%s slot0=%s bytes=%s' % (hx(vt), hx(s0), read_va(s0,8).hex()))
print('== 副表 slot0（thunk 对照）==')
for vt in (0x007E7EB0, 0x007E8278, 0x007ECD68, 0x007E7E8C):
    s0 = u32(vt)
    print('  vt=%s slot0=%s bytes=%s' % (hx(vt), hx(s0), read_va(s0,8).hex()))
