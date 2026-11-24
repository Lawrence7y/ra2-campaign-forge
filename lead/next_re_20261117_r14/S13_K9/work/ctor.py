# Examine the two-stage constructor at 0x438540-0x4385a0 and call-site functions
import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
print('=== ctor 0x438540 ===')
for i in md.disasm(rd(0x438540,0x4385c0-0x438540),0x438540):
    print(hex(i.address),i.mnemonic,i.op_str)
print('=== ctor 0x40b540 (F1a) ===')
for i in md.disasm(rd(0x40b540,0x40b630-0x40b540),0x40b540):
    print(hex(i.address),i.mnemonic,i.op_str)
