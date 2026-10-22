"""Disassembly helper: print instructions at a VA from gamemd.exe.

Read-only. Used to adjudicate symbol conflicts and to seed the knowledge base
with byte-level evidence. Kept deliberately small: no control-flow recovery,
just a linear window with correct VA->file mapping.
"""

import struct
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"


def load(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    opt_size = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    image_base = struct.unpack_from("<I", blob, opt + 28)[0]
    sec_tab = opt + opt_size
    secs = []
    for i in range(nsec):
        off = sec_tab + i * 40
        name = blob[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", blob, off + 8)
        secs.append((name, vaddr, vsize, rawptr, rawsize))
    return blob, image_base, secs


BLOB, IMAGE_BASE, SECS = load(EXE)


def read_va(va, n):
    rva = va - IMAGE_BASE
    for name, vaddr, vsize, rawptr, rawsize in SECS:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            d = rva - vaddr
            if d >= rawsize:
                return b""
            return BLOB[rawptr + d: rawptr + d + n]
    return b""


def disasm(va, count=12):
    code = read_va(va, count * 8 + 32)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    out = []
    for insn in md.disasm(code, va):
        out.append(f"0x{insn.address:08X}  {insn.bytes.hex(' '):<24} {insn.mnemonic} {insn.op_str}".rstrip())
        if len(out) >= count:
            break
    return out


def main():
    for arg in sys.argv[1:]:
        va = int(arg, 16)
        print(f"=== 0x{va:08X} ===")
        print("  bytes:", read_va(va, 16).hex(" "))
        for line in disasm(va):
            print("  " + line)
        print()


main()
