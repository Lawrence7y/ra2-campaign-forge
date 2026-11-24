
import sys; sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K5\_audit')
from a_lib2 import *
print('== 0x46B5C0 (precedent, [已证]) =='); show(0x46B5C0,maxins=600)
print()
print('imm at 0x75D0BA area:')
for ins in MD.disasm(read(0x75D0B4,16),0x75D0B4):
    print(fmt(ins))
print()
print('slot8 of VT 0x7f6b30 =',hex(u32(0x7f6b30+0x20)))
print('slot8 of VT 0x7e3d10 =',hex(u32(0x7e3d10+0x20)))
