"""Scan BuildingClass destructor 0x43BCF0 disassembly for slot73 (+0x124) calls,
push 0, and check callee 0x45AE10 (array delete)."""
import w156_core as C
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

print("=== 0x43BCF0 (BuildingClass dtor) full disasm, annotated ===")
insns = C.disas_fn(0x43BCF0, cap=3000)
for ins in insns:
    mark = ""
    # any [reg + 0x124] operand -> slot73
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.disp == 0x124:
            mark += " <<< SLOT73(0x124)"
    if ins.mnemonic == 'push' and ins.op_str.strip() in ('0','0x0'):
        mark += " [PUSH0]"
    if ins.mnemonic == 'call':
        mark += " [CALL]"
    if mark:
        print("  " + C.fmt(ins) + mark)
print("\n--- total insns =", len(insns))
print("\n=== all call instructions in 0x43BCF0 ===")
for ins in insns:
    if ins.mnemonic == 'call':
        print("  " + C.fmt(ins))

print("\n=== 0x45AE10 (array delete primitive) disasm ===")
for ins in C.disas_fn(0x45AE10, cap=1000):
    print("  " + C.fmt(ins))
