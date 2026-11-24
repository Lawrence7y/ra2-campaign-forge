# W99 Task1: byte-level re-verification of the crash-family functions.
# Ranges: 0x0047C4A0..0x0047C580 (covers 0x0047C4D0 sibling and 0x0047C520..0x0047C54E family)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import disas, read, secof

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task1_family_disas.txt"
START, END = 0x0047C4A0, 0x0047C580

lines = []
lines.append("W99 Task1: crash family disassembly 0x%08X..0x%08X (raw bytes per insn)" % (START, END))
lines.append("section of start: %s" % (secof(START),))
lines.append("")
for va, bh, mn, ops, insn in disas(START, END):
    lines.append("0x%08X: %-20s %s %s" % (va, bh, mn, ops))

# byte verification of the three key claims
lines.append("")
lines.append("=== key byte checks ===")
# 0x0047C52A: mov esi,[ecx+0xE4] => bytes should be 8B B1 E4 00 00 00
b = read(0x0047C52A, 6)
lines.append("bytes@0x0047C52A (6) = %s  (expect 8B B1 E4 00 00 00 = mov esi,[ecx+0xE4])" % b.hex().upper())
# 0x0047C538 region: dump 0x0047C530..0x0047C544
b = read(0x0047C530, 0x14)
lines.append("bytes@0x0047C530 (0x14) = %s" % b.hex().upper())
# 0x0047C53B region
b = read(0x0047C53B, 8)
lines.append("bytes@0x0047C53B (8) = %s" % b.hex().upper())
# sibling wanted-id 0x24 check: find imm 0x24 inside 0x0047C4D0..0x0047C520
lines.append("")
lines.append("=== imm constant scan in sibling 0x0047C4D0..0x0047C520 ===")
for va, bh, mn, ops, insn in disas(0x0047C4D0, 0x0047C520):
    if "0x24" in ops:
        lines.append("0x%08X: %-20s %s %s" % (va, bh, mn, ops))

txt = "\n".join(lines) + "\n"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
