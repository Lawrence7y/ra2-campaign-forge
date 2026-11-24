"""AUDIT7: dump an arbitrary function body by entry VA."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *


def fn(entry, max_insn=400):
    o = va2off(entry)
    out = []
    for insn in md.disasm(DATA[o:o + 6000], entry):
        out.append(insn)
        if len(out) >= max_insn:
            break
        if insn.mnemonic.startswith('ret'):
            nx = DATA[va2off(insn.address) + insn.size: va2off(insn.address) + insn.size + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nx) or len(nx) < 4:
                break
        if insn.mnemonic == 'jmp' and insn.operands and insn.operands[0].type == 2 and insn.operands[0].imm < entry:
            pass
    return out


if __name__ == '__main__':
    for a in sys.argv[1:]:
        va = int(a, 16)
        print(f"\n===== {va:08X} =====")
        for i in fn(va):
            print(f"{i.address:08X}  {i.bytes.hex(' '):<24} {i.mnemonic} {i.op_str}")
