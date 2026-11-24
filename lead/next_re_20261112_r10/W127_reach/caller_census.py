#!/usr/bin/env python3
"""W127d: independent (capstone) caller census for the 20 sites' enclosing functions,
plus resolution of the 0x6D1570 orphan region.

Discipline: this does NOT trust Ghidra's caller lists. It decodes every E8/E9 in
.text and tallies targets, then compares with what Reach20.java reported.
"""
import struct
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
TEXT_VA, TEXT_END = 0x00401000, 0x007E038D
text = img[TEXT_VA - ib:TEXT_END - ib]

FNS = {
    0x00654320: "site1",
    0x006ABD30: "site2,3",
    0x006D04F0: "site4,5,6",
    0x006D0680: "site7,8,9",
    0x006D09C0: "site10",
    0x006D1200: "site11-14",
    0x006D14F0: "site15,16",
    0x006D1570: "site17 (orphan region start, candidate)",
    0x006D1610: "site18",
    0x006D1660: "site19,20",
    0x006922E0: "caller of 6d0680",
    0x004FC0B0: "crash entry",
}

print("=== [A] independent E8/E9 target census (whole .text) ===")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True   # linear sweep over .text hits data/padding; without this the
                     # disassembler STOPS at the first undecodable byte (155K/1.1M insns)
n_insn = n_call = 0
calls = {k: [] for k in FNS}
for ins in md.disasm(text, TEXT_VA):
    n_insn += 1
    if ins.mnemonic not in ("call", "jmp"):
        continue
    if not ins.op_str.startswith("0x"):
        continue
    dst = int(ins.op_str, 16)
    n_call += 1
    if dst in calls:
        calls[dst].append((ins.address, ins.mnemonic))
print("swept %d instructions, %d call/jmp with direct target" % (n_insn, n_call))

for va, label in FNS.items():
    hits = calls[va]
    print("\n  FUN_%08X  (%s): %d direct %s" % (va, label, len(hits),
          "entry" if hits else "REFERENCES"))
    for a, m in hits[:10]:
        print("      %s @0x%08X" % (m, a))
    if len(hits) > 10:
        print("      ... (%d total)" % len(hits))

print("\n=== [B] region 0x6D15CB .. 0x6D1625 (tail of orphan + FUN_006d1610) ===")
for ins in md.disasm(img[0x006D15CB - ib:0x006D1625 - ib], 0x006D15CB):
    print("   %08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("\n=== [C] who references 0x6D1605 / 0x6D15FA as a call target? ===")
for tgt in (0x006D15FA, 0x006D1570, 0x006D15E0, 0x006D1605):
    pat = struct.pack("<I", tgt)
    n_imm = text.count(pat)
    print("  0x%08X: immediate dword occurrences in .text = %d" % (tgt, n_imm))
