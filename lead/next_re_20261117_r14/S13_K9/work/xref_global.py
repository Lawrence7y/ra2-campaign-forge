# exhaustive: all code xrefs to the cited global 0x89C668, and all 'mov ecx,imm32' where imm is a known vptr-holding global
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
from capstone.x86 import *
T0,T1=text_range(); code=rd(T0,T1-T0)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(code,T0))
# xrefs to 0x89C668 as immediate operand
G=0x89c668
print('=== instructions referencing 0x89C668 ===')
for i in insns:
    for op in i.operands:
        if op.type==X86_OP_IMM and (op.imm&0xffffffff)==G:
            print(hex(i.address),i.mnemonic,i.op_str,'|',i.bytes.hex())
        if op.type==X86_OP_MEM and (op.mem.disp&0xffffffff)==G:
            print(hex(i.address),i.mnemonic,i.op_str,'|',i.bytes.hex())
