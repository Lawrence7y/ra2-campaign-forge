# W99 Task3c: (1) rest of wrapper 0x568940..0x568BB0
#             (2) E8 callers of 0x5687F0 (removal) and 0x5683C0 (link wrapper) with contexts
#             (3) class-6 vtable 0x7E3EBC slots +0x78/+0x88/+0x108 disasm
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import disas, dword, PE, IMAGEBASE

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task3c_removal_chain.txt"
L = []

with open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb") as f:
    blob = f.read()
for s in PE.sections:
    if s.Name.rstrip(b"\x00").decode() == ".text":
        base = IMAGEBASE + s.VirtualAddress
        raw = blob[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]

def e8_callers(target):
    res = []
    i = 0
    n = len(raw)
    while i < n - 5:
        if raw[i] == 0xE8:
            rel = struct.unpack("<i", raw[i+1:i+5])[0]
            if base + i + 5 + rel == target:
                res.append(base + i)
        i += 1
    return res

def dump(lo, hi, title, marks=()):
    L.append("=== %s ===" % title)
    for va, bh, mn, ops, insn in disas(lo, hi):
        mark = "  <<<<" if va in marks else ""
        L.append("0x%08X: %-22s %s %s%s" % (va, bh, mn, ops, mark))
    L.append("")

dump(0x568940, 0x568BB0, "removal wrapper rest 0x568940..0x568BB0", marks=(0x568940,))

L.append("=== E8 callers of removal 0x5687F0 ===")
for c in e8_callers(0x5687F0):
    L.append("  0x%08X" % c)
L.append("")
L.append("=== E8 callers of link-wrapper fn start 0x5683C0 ===")
for c in e8_callers(0x5683C0):
    L.append("  0x%08X" % c)
L.append("")

for site in e8_callers(0x5687F0)[:8]:
    dump(site - 0x50, site + 0x14, "removal-caller context @0x%08X" % site, marks=(site,))

L.append("=== class-6 vtable 0x7E3EBC slot disasm ===")
for off in (0x78, 0x88, 0x108, 0xF4, 0xC0):
    val, b = dword(0x7E3EBC + off)
    line = "slot +0x%03X = 0x%08X:" % (off, val)
    L.append(line)
    try:
        for va, bh, mn, ops, insn in disas(val, val + 0x10)[:4]:
            L.append("    0x%08X: %-16s %s %s" % (va, bh, mn, ops))
    except Exception as e:
        L.append("    <err %s>" % e)

txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt[:13000])
print("... full at", OUT)
