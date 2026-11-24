#!/usr/bin/env python3
"""W127b: characterize the non-stock .detour section of gamemd.exe.

Why it matters: ②-a (§822-1) concluded the FUN_00724730 entry guard needs a
trampoline because the 7 bytes before the fault have no inline room. A static,
executable, partly-empty .detour section in the SAME image would be a ready-made
code cave -- and its presence means this exe is already statically modified.
"""
import pefile
import re
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()


def flags(ch):
    return ("R" if ch & 0x40000000 else "-") + ("W" if ch & 0x80000000 else "-") + \
           ("X" if ch & 0x20000000 else "-") + ("C" if ch & 0x00000020 else "-")


print("=== sections ===")
for s in pe.sections:
    n = s.Name.rstrip(b"\x00").decode(errors="replace")
    print("  %-8s VA=0x%08X vsize=0x%-7X raw=0x%-7X char=0x%08X %s"
          % (n, ib + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData,
             s.Characteristics, flags(s.Characteristics)))

print("\n=== headers ===")
print("  ImageBase           : 0x%08X" % ib)
print("  AddressOfEntryPoint : 0x%08X" % (ib + pe.OPTIONAL_HEADER.AddressOfEntryPoint))
print("  is DLL              : %s" % bool(pe.FILE_HEADER.Characteristics & 0x2000))
print("  SizeOfImage         : 0x%08X" % pe.OPTIONAL_HEADER.SizeOfImage)
print("  NumberOfSections    : %d" % pe.FILE_HEADER.NumberOfSections)
print("  TimeDateStamp       : 0x%08X" % pe.FILE_HEADER.TimeDateStamp)
print("  checksum            : 0x%08X (stored) vs 0x%08X (file)"
      % (pe.OPTIONAL_HEADER.CheckSum, pe.generate_checksum()))
for dd in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
    if dd.VirtualAddress:
        print("  dir %-14s VA=0x%08X size=0x%X" % (dd.name, dd.VirtualAddress, dd.Size))

d = next(s for s in pe.sections if s.Name.rstrip(b"\x00") == b".detour")
va = ib + d.VirtualAddress
size = d.Misc_VirtualSize
blob = img[va - ib: va - ib + size]

print("\n=== .detour ===")
print("  VA=0x%08X size=0x%X (%d bytes)  rawsize=0x%X"
      % (va, size, size, d.SizeOfRawData))
nz = sum(1 for b in blob if b != 0)
print("  nonzero bytes: %d/%d (%.1f%% empty)" % (nz, size, 100.0 * (size - nz) / size))

print("\n  first 192 bytes:")
for i in range(0, min(192, size), 16):
    print("    %08X  %s" % (va + i, blob[i:i + 16].hex(" ")))

print("\n  ASCII strings:")
for m in re.finditer(rb"[ -~]{5,}", blob):
    print("    str@0x%08X: %r" % (va + m.start(), m.group().decode()))

# how many callers/jumps INTO .detour from .text?
t = next(s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text")
tva = ib + t.VirtualAddress
tblob = img[tva - ib: tva - ib + t.Misc_VirtualSize]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
refs = []
for ins in md.disasm(tblob, tva):
    if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        dst = int(ins.op_str, 16)
        if va <= dst < va + size:
            refs.append((ins.address, ins.mnemonic, dst))
print("\n  calls/jmps from .text into .detour: %d" % len(refs))
for r in refs[:40]:
    print("    0x%08X %s -> 0x%08X" % r)

# disassemble the populated part of .detour
print("\n  disassembly of first nonzero region:")
first = next((i for i, b in enumerate(blob) if b), 0)
for ins in md.disasm(blob[first:first + 160], va + first):
    print("    %08X  %-24s %s %s" % (ins.address, ins.bytes.hex(),
                                     ins.mnemonic, ins.op_str))
