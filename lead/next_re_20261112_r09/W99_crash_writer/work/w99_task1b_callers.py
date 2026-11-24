# W99 Task1b: finish variant3, find direct call/jmp sites to the family,
# and census the guard fingerprint "mov al,[0xA8E9A0]" (A0 A0 E9 A8 00).
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import read, disas, va2off, PE, IMAGEBASE

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task1b_variant3_callers_guard.txt"
lines = []

# ---- 1. finish variant 3 (0x0047C57E .. 0x0047C5B0)
lines.append("=== variant 3 tail 0x0047C57E..0x0047C5B0 ===")
for va, bh, mn, ops, insn in disas(0x0047C57E, 0x0047C5B0):
    lines.append("0x%08X: %-20s %s %s" % (va, bh, mn, ops))

# ---- 2. direct call/jmp census across whole .text (raw E8/E9 scan, false-positive tolerant)
sect = None
for s in PE.sections:
    if s.Name.rstrip(b"\x00").decode() == ".text":
        sect = s
text_va = IMAGEBASE + sect.VirtualAddress
text_raw = read(text_va, sect.SizeOfRawData)

TARGETS = {0x0047C520: "f520(WhatAmI==6, chain E4)",
           0x0047C4D0: "f4d0(param id, chain E4/E8)",
           0x0047C550: "f550(const 0x24, chain E4/E8)"}
lines.append("")
lines.append("=== direct E8/E9 references to family (raw scan; may contain intra-instr false positives) ===")
for tgt, name in TARGETS.items():
    lines.append("-- target 0x%08X (%s)" % (tgt, name))
    for i in range(len(text_raw) - 5):
        b = text_raw[i]
        if b in (0xE8, 0xE9):
            rel = struct.unpack("<i", text_raw[i+1:i+5])[0]
            site = text_va + i
            if site + 5 + rel == tgt:
                lines.append("  site 0x%08X: %s (rel) -> 0x%08X" % (site, "call" if b == 0xE8 else "jmp", tgt))

# ---- 3. guard fingerprint census: A0 A0 E9 A8 00 anywhere in .text raw bytes
lines.append("")
lines.append("=== guard fingerprint A0A0E9A800 (mov al,[0xA8E9A0]) census in .text ===")
pat = bytes.fromhex("A0A0E9A800")
hits = []
i = 0
while True:
    j = text_raw.find(pat, i)
    if j < 0:
        break
    hits.append(text_va + j)
    i = j + 1
lines.append("count = %d" % len(hits))
for h in hits:
    # disassemble 3 instructions from each hit for context
    try:
        ctx = disas(h, h + 24)[:3]
        s = " | ".join("%s %s" % (m, o) for _, _, m, o, _ in ctx)
    except Exception as e:
        s = "<disas err %s>" % e
    lines.append("  0x%08X: %s" % (h, s))

txt = "\n".join(lines) + "\n"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
