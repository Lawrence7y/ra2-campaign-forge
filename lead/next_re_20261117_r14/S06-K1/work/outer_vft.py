from pehelp import *
for ins in disasm(0x63f6b0, 0x180, count=120):
    if ins.mnemonic=='mov' and ins.operands and len(ins.operands)==2:
        o0,o1=ins.operands
        if o0.type==X86_OP_MEM and o0.mem.disp==0 and o0.mem.base in (0,):
            print("VFT WRITE?",fmt(ins))
        if o0.type==X86_OP_IMM and 0x7e0000<=o0.imm<0x7f0000:
            print("VFT-IMM:",fmt(ins))
    if ins.mnemonic=='ret':
        print("RET:",fmt(ins)); break
print("--- all mov [esi],imm near start ---")
for ins in disasm(0x63f6b0, 0x200, count=140):
    ops=ins.operands
    if ins.mnemonic=='mov' and len(ops)==2 and ops[0].type==X86_OP_MEM and ops[0].mem.disp==0 and ops[1].type==X86_OP_IMM:
        print(fmt(ins))
