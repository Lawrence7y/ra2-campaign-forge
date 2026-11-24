"""S13-K1: byte-by-byte disassembly of Warhead resolution and Verses parsing windows."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import disasm, fmt_insn, cstr, u32

def dump(title, va, n):
    print("###", title, hex(va), "..", hex(va+n))
    for i in disasm(va, n, skipdata=True):
        extra = ""
        # annotate push immediate strings
        if i.mnemonic == "push" and i.operands and i.operands[0].type == 2:
            s = cstr(i.operands[0].imm & 0xFFFFFFFF, 48)
            if s and all(0x20 < ord(c) < 0x7F for c in s) and len(s) > 1:
                extra = "   ; '%s'" % s
        print("  " + fmt_insn(i) + extra)
    print()

dump("WeaponTypeClass Warhead resolution", 0x772940, 0xA5)
dump("WarheadTypeClass Verses region", 0x75DD00, 0x1BE)
