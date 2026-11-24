# W99 Task2f: classify every byte-scan +0xE4 write site. Context +-0x48, plus
# flags: walks +0x30? vptr stores nearby? guard [0xA8E9A0]?
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import disas

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2f_write_classify.txt"
SITES = [0x004358A9, 0x00436A2D, 0x0047BBA7, 0x0047BC82, 0x0047E91F, 0x0047EACF,
         0x0048E846, 0x0048EE2A, 0x0048FC00, 0x004908AC, 0x00511451,
         0x00565E61, 0x00566673, 0x0065AEF5, 0x006657B7, 0x00671CFF,
         0x006F07B7, 0x006F105D, 0x006F14E6, 0x006F1501, 0x006F4761,
         0x00721740, 0x00721C6F, 0x00721CD0, 0x0074C623, 0x0074C7B2]
L = []
for site in SITES:
    L.append("=" * 74)
    L.append("SITE 0x%08X" % site)
    lo, hi = site - 0x48, site + 0x30
    for va, bh, mn, ops, insn in disas(lo, hi):
        mark = "  <<<<" if va == site else ""
        L.append("0x%08X: %-22s %s %s%s" % (va, bh, mn, ops, mark))
    L.append("")
txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt[:12000])
print("... full at", OUT)
