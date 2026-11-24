# exhaustive xrefs with skipdata guard
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
from capstone.x86 import *
T0,T1=text_range(); code=rd(T0,T1-T0)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(code,T0))
def ops(i):
    if i.id==X86_INS_INVALID: return []
    try: return i.operands
    except: return []
G=0x89c668
print('=== instructions referencing 0x89C668 ===')
cnt=0
for i in insns:
    for op in ops(i):
        if op.type==X86_OP_IMM and (op.imm&0xffffffff)==G:
            print(hex(i.address),i.mnemonic,i.op_str,'|',i.bytes.hex());cnt+=1
        if op.type==X86_OP_MEM and (op.mem.disp&0xffffffff)==G:
            print(hex(i.address),i.mnemonic,i.op_str,'|',i.bytes.hex());cnt+=1
print('count',cnt)
