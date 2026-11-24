from re_core import *
from capstone.x86 import X86_OP_IMM
def call_targets(va,n):
    out=[]
    for i in dis(va,n):
        if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_IMM: out.append((i.address,i.operands[0].imm))
    return out
for va,n in [(0x75cec0,1200),(0x46bbc0,1400)]:
    print(hex(va),[hex(x[1]) for x in call_targets(va,n)])
print("\nMOV IMMed VPTR in ctors")
for va,n in [(0x75cec0,1200),(0x46bbc0,1400)]:
    print(hex(va))
    for i in dis(va,n):
        if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==2 and i.operands[1].type==X86_OP_IMM and 0x7e1000<=i.operands[1].imm<0x812000:
            print(fmt(i))
print("\nRTTI TD Containers around suspected")
for td in [0x818c18,0x836640]:
    print(hex(td),repr(cstr(td+8)))
print("\nVT refs")
for vt in [0x7e3d10,0x7ef890,0x7f0810,0x7f6b30,0x7f73b8]:
    pat=struct.pack('<I',vt)
    print(hex(vt),[hex(x) for x in find_bytes(pat)][:20], 'count',len(find_bytes(pat)))
