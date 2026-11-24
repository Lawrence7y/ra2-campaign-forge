"""s2: dump raw bytes + linear disassembly (capstone, skipdata=True) of one
0x80-byte window per slot; compute per-slot md5 for template identity.

Usage:  python s2_bodies.py [--all]
"""
import hashlib
import sys

import capstone

import pe

ENTRIES = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
           "00680070", "006800F0", "00680170", "006801F0", "00680270",
           "006802F0", "00680370", "006803F0", "00680470", "006804F0",
           "00680570", "00680670", "006806F0", "00680770", "006807F0",
           "00680870", "006808F0", "00680970", "006809F0", "00680A70",
           "00680AF0", "00680B70", "00680BF0", "00680C70", "00680CF0",
           "00680D70", "00680DF0", "00680E70", "00680EF0"]
SAMPLE = ["0067FDF0", "006800F0", "00680470", "006807F0", "00680B70", "00680EF0"]
EXTRA = ["006805F0"]      # the alleged missing #17 slot
WINDOW = 0x80


def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.skipdata = True
    return m


def disasm(p, va, n=WINDOW):
    data = p.raw(va, n)
    return list(md().disasm(data, va))


def dump_one(p, va, label):
    print(f"\n=== {label}  entry 0x{va:08X}  raw {WINDOW} B "
          f"md5(0x7F)={hashlib.md5(p.raw(va, 0x7F)).hexdigest()} "
          f"md5(0x80)={hashlib.md5(p.raw(va, 0x80)).hexdigest()}")
    print(p.hexdump(va, WINDOW))
    print("--- disasm")
    for ins in disasm(p, va):
        off = ins.address - va
        print(f"  +0x{off:02X}  {ins.address:08X}  "
              f"{' '.join(f'{b:02X}' for b in ins.bytes):<20} "
              f"{ins.mnemonic:<7} {ins.op_str}")


def main():
    p = pe.open_pe()
    print("sha256", p.sha256)
    if "--all" in sys.argv:
        for e in ENTRIES:
            print(f"{e}  0x7F={hashlib.md5(p.raw(int(e,16),0x7F)).hexdigest()}"
                  f"  full0x80={hashlib.md5(p.raw(int(e,16),0x80)).hexdigest()}")
        return
    for e in SAMPLE + EXTRA:
        dump_one(p, int(e, 16), e)


if __name__ == "__main__":
    main()
