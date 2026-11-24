from capstone import *
from capstone.x86_const import X86_OP_MEM
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
for b in [bytes.fromhex('ff525c'), bytes.fromhex('ff945c01000000'), bytes.fromhex('ff545c10'), bytes.fromhex('ff925cffffff')]:
    for i in md.disasm(b,0x1000):
        print(b.hex(), i.mnemonic, repr(i.op_str), [(hex(x.mem.disp & 0xffffffff), x.mem.base, x.mem.index) for x in i.operands if x.type==X86_OP_MEM])
