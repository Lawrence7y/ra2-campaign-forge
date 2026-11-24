"""dump_range.py — linear disassembly dump of an arbitrary VA range.

usage: python dump_range.py 0x4D0750 0x4D07C0 [label]
"""
import os
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe


def dump(pe, md, va, end, label=""):
    L = [f"---- {label} {va:#010x}..{end:#010x} ----"]
    pc = va
    while pc < end:
        got = list(md.disasm(pe.bytes_at(pc, min(16, end - pc)), pc, 1))
        if not got:
            L.append(f"{pc:#010x}  !! db {pe.u8(pc):#04x}")
            pc += 1
            continue
        ins = got[0]
        L.append(f"{pc:#010x}  {ins.bytes.hex().upper():<20} {ins.mnemonic:<7} {ins.op_str}")
        pc += ins.size
    return "\n".join(L)


if __name__ == "__main__":
    pe = open_pe()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    va = int(sys.argv[1], 16)
    end = int(sys.argv[2], 16)
    label = sys.argv[3] if len(sys.argv) > 3 else ""
    print(dump(pe, md, va, end, label))
