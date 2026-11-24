# W99 Task2d: identity work.
# (a) contexts of class-6 ctor sites 0x43B721/0x43B9FC/0x43BCFF (object size hunt)
# (b) callers of f520: how is ecx (the chain head owner) computed? sites near infantry / map
# (c) function containing lea edx,[esi+0xE4] at 0x436992
# (d) 0x00436C00..0x00437010 sampling: are these +0x30 chain walkers too?
# (e) full disasm of 0x0051BF90 IsCellOccupied (bounded 0x200, stop early)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import disas

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2d_identity.txt"
L = []

def dump(lo, hi, title, mark=None):
    L.append("=== %s ===" % title)
    for va, bh, mn, ops, insn in disas(lo, hi):
        m = "  <<<<" if (mark and va == mark) else ""
        L.append("0x%08X: %-22s %s %s%s" % (va, bh, mn, ops, m))
    L.append("")

dump(0x0043B6F0, 0x0043B760, "class6 ctor site A 0x43B721", 0x0043B721)
dump(0x0043B9D0, 0x0043BA30, "class6 ctor site B 0x43B9FC", 0x0043B9FC)
dump(0x0043BCD0, 0x0043BD40, "class6 ctor site C 0x43BCFF", 0x0043BCFF)

# (b) caller contexts: pick representative f520 call sites
for site, ttl in [(0x0051BD11, "f520 caller @0x51BD11 (Infantry region)"),
                  (0x00452B10, "f520 caller @0x452B10"),
                  (0x006D57A7, "f520 caller @0x6D57A7"),
                  (0x0073A5B7, "f520 caller @0x73A5B7"),
                  (0x00417ED3, "f520 caller @0x417ED3")]:
    dump(site - 0x40, site + 0x14, ttl, site)

dump(0x00436940, 0x004369E0, "(c) fn with lea edx,[esi+0xE4] @0x436992")
dump(0x00436C00, 0x00436CA0, "(d) 0x436Cxx chain-walker sample")
dump(0x00436FF0, 0x00437040, "(d) 0x43700x chain-walker sample")

# (e) IsCellOccupied
L.append("=== (e) 0x0051BF90 IsCellOccupied (first 0x140 bytes) ===")
n = 0
for va, bh, mn, ops, insn in disas(0x0051BF90, 0x0051BF90 + 0x140):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))
    n += 1

txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
