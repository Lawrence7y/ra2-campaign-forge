# W99 Task2b: context dumps around every +0xE4/+0xE8 object-write site,
# plus function-start heuristic (scan back for C3/C2 + int3 padding).
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import read, disas, va2off

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2b_write_site_contexts.txt"

SITES = [0x0041F86F, 0x004358A9, 0x00436A2D, 0x0046780B,
         0x0045FE18, 0x0045FE36, 0x004689CB, 0x00468AE5]
CTXT = 0x60  # bytes before/after

def func_start_hint(va, maxback=0x1200):
    """walk back to nearest C3/C2 followed by >=2 bytes of CC/90 padding; return (va, note)"""
    code = read(va - maxback, maxback)
    i = len(code) - 1
    while i > 8:
        b = code[i]
        if b == 0xC3 or b == 0xC2:
            # check padding after it
            j = i + (4 if b == 0xC2 else 1)
            pad = 0
            while j < len(code) and code[j] in (0xCC, 0x90):
                pad += 1
                j += 1
            if pad >= 2 and j < len(code):
                return va - maxback + j, ("after %s + %d pad" % ("C3" if b == 0xC3 else "C2", pad))
        i -= 1
    return None, "no boundary found within 0x%X" % maxback

lines = []
for site in SITES:
    lines.append("=" * 78)
    lines.append("SITE 0x%08X" % site)
    fs, note = func_start_hint(site)
    lines.append("func-start hint: %s (%s)" % (("0x%08X" % fs) if fs else "None", note))
    lo, hi = site - CTXT, site + CTXT
    for va, bh, mn, ops, insn in disas(lo, hi):
        mark = "  <<<<" if va == site else ""
        lines.append("0x%08X: %-22s %s %s%s" % (va, bh, mn, ops, mark))
    lines.append("")

txt = "\n".join(lines) + "\n"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
