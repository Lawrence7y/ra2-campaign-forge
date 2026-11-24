"""s5: dump Save_Core 0x67D300 and find how it reaches the 35 slots.

The slots are not reached by `call rel32`; this script linear-sweeps Save_Core
and prints every instruction, so the actual transfer mechanism is visible in
bytes.
"""
import sys

import capstone

import pe

SAVE_CORE = 0x0067D300
SLOTS = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
         "00680070", "006800F0", "00680170", "006801F0", "00680270",
         "006802F0", "00680370", "006803F0", "00680470", "006804F0",
         "00680570", "006805F0", "00680670", "006806F0", "00680770",
         "006807F0", "00680870", "006808F0", "00680970", "006809F0",
         "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
         "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0"]


def main():
    n = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x140
    start = int(sys.argv[2], 0) if len(sys.argv) > 2 else SAVE_CORE
    p = pe.open_pe()
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    slot = {int(s, 16) for s in SLOTS}
    for ins in m.disasm(p.raw(start, n), start):
        mark = ""
        if ins.mnemonic in ("call", "jmp"):
            op = ins.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and op.imm in slot:
                mark = "   <== SLOT"
            elif op.type == capstone.x86.X86_OP_MEM and not op.mem.base:
                mark = f"   (ind IAT 0x{op.mem.disp:08X})"
        for k, op in enumerate(ins.operands):
            if op.type == capstone.x86.X86_OP_IMM and op.imm in slot:
                mark += "   <== SLOT VA in operand"
        print(f"{ins.address:08X}  {' '.join(f'{b:02X}' for b in ins.bytes):<26} "
              f"{ins.mnemonic:<8} {ins.op_str}{mark}")


if __name__ == "__main__":
    main()
