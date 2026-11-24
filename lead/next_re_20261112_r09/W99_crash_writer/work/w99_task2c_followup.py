# W99 Task2c: (1) lea/address-taken sites with disp 0xE4/0xE8 (hidden indirect writes)
#             (2) full listing of all +0xE4 READ sites
#             (3) clean disasm of function at 0x00435820 and around 0x0041F86F
#             (4) vtable identity checks: 0x7E3AD0/0x7E3AB4/0x7E3AAC/0x7E3AA4 slot11 (WhatAmI)
#             (5) find constructor sites storing vptr 0x007E3EBC (class id 6) in .text
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import read, disas, dword, PE, IMAGEBASE, MD

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2c_followup.txt"
rows = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2_disp_census.json"))
L = []

L.append("=== (1) lea with disp 0xE4/0xE8 (address-taken; potential hidden writes) ===")
for r in rows:
    if r["disp"] in ("0xE4", "0xE8") and r["text"].startswith("lea"):
        L.append("%s %s: %s" % (r["va"], r["bytes"], r["text"]))

L.append("")
L.append("=== (2) ALL +0xE4 read sites ===")
for r in rows:
    if r["disp"] == "0xE4" and not r["is_write"]:
        L.append("%s %-22s %s" % (r["va"], r["bytes"], r["text"]))

L.append("")
L.append("=== (3a) clean disasm 0x00435820..0x00435940 (ctor candidate) ===")
for va, bh, mn, ops, insn in disas(0x00435820, 0x00435940):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

L.append("")
L.append("=== (3b) context 0x0041F86F, aligned from 0x0041F840 ===")
for va, bh, mn, ops, insn in disas(0x0041F840, 0x0041F8B0):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

L.append("")
L.append("=== (4) vtable slot11 (WhatAmI) checks ===")
for vt in (0x7E3AD0, 0x7E3AB4, 0x7E3AAC, 0x7E3AA4, 0x007E3EBC, 0x7E16B0):
    val, b = dword(vt + 0x2C)
    L.append("vtable 0x%08X: [+0x2C] = 0x%08X  bytes=%s" % (vt, val, b.hex().upper()))
    try:
        ins = list(disas(val, val + 8))
        for va, bh, mn, ops, insn in ins[:2]:
            L.append("    0x%08X: %-14s %s %s" % (va, bh, mn, ops))
    except Exception as e:
        L.append("    <disas err %s>" % e)

L.append("")
L.append("=== (5) ctor sites storing vptr 0x007E3EBC (class 6) in .text ===")
with open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb") as f:
    blob = f.read()
for s in PE.sections:
    if s.Name.rstrip(b"\x00").decode() != ".text":
        continue
    base = IMAGEBASE + s.VirtualAddress
    raw = blob[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
    pat = struct.pack("<I", 0x007E3EBC)
    i = 0
    n = 0
    while True:
        j = raw.find(pat, i)
        if j < 0:
            break
        site = base + j
        # back up up to 3 bytes for opcode prefix (C7 0x / 89 0x / A3 / 89 ...)
        L.append("-- hit at 0x%08X, preceding bytes: %s" % (site, raw[max(0, j-3):j].hex().upper()))
        n += 1
        i = j + 1
    L.append("total hits of dword 0x007E3EBC in .text: %d" % n)

# context around each hit (disasm 0x20 before .. 0x10 after, best-effort alignment)
L.append("")
i = 0
shown = 0
for s in PE.sections:
    if s.Name.rstrip(b"\x00").decode() != ".text":
        continue
    base = IMAGEBASE + s.VirtualAddress
    raw = blob[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
    pat = struct.pack("<I", 0x007E3EBC)
    while True:
        j = raw.find(pat, i)
        if j < 0:
            break
        site = base + j
        prev = raw[max(0, j-3):j].hex().upper()
        if prev.startswith("C7"):  # mov [reg/mem], imm32 ctor pattern
            L.append("ctor-ish site 0x%08X (prev=%s):" % (site, prev))
            try:
                for va, bh, mn, ops, insn in disas(site - 0x20, site + 0x14):
                    L.append("  0x%08X: %-18s %s %s" % (va, bh, mn, ops))
            except Exception as e:
                L.append("  <disas err %s>" % e)
            shown += 1
        i = j + 1
L.append("ctor-ish sites shown: %d" % shown)

txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
