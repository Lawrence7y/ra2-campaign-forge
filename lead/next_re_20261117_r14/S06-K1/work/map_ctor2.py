from pehelp import *
# Find function boundaries around 0x56516f by scanning back for ret/int3 padding
def find_start(addr, back=0x2000):
    ins=list(disasm(addr-back, back+16))
    # find last index where prior instr ends with ret and following are nops/int3
    cand=None
    for i,insn in enumerate(ins):
        if insn.address>=addr: break
        if insn.mnemonic in ('ret','retf') and i+1<len(ins):
            nxt=ins[i+1]
            if nxt.mnemonic in ('nop','int3'):
                cand=nxt.address
    return cand
for a in [0x56516f,0x565268,0x5652c7]:
    print(f"start before {a:#x}: {find_start(a) and hex(find_start(a))}")

# Wider view: dump from 0x564f00 to 0x565180 focusing on push imm and calls
print("\n=== all 'push imm' in 0x564000..0x565180, with following call ===")
for ins in disasm(0x564000, 0x1200):
    if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
        im=ins.operands[0].imm
        if im>=0x100:
            # next few instrs
            nxt=[]
            for j in disasm(ins.address+ins.size, 24, count=5):
                nxt.append(f"{j.mnemonic} {j.op_str}")
            print(f"  {fmt(ins)}  -> {'; '.join(nxt[:3])}")
