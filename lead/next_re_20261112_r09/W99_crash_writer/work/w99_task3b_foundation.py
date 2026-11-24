# W99 Task3b: (1) context + function start of the sole unlink caller wrapper 0x5688EB
#             (2) E8 callers of link 0x47E8A0 and of the wrapper's entry
#             (3) hunt double-loop foundation patterns near those callers
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import disas, PE, IMAGEBASE

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task3b_foundation.txt"
L = []

def sect():
    for s in PE.sections:
        if s.Name.rstrip(b"\x00").decode() == ".text":
            return IMAGEBASE + s.VirtualAddress, None
def blob_text():
    for s in PE.sections:
        if s.Name.rstrip(b"\x00").decode() == ".text":
            with open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb") as f:
                f.seek(s.PointerToRawData)
                return IMAGEBASE + s.VirtualAddress, f.read(s.SizeOfRawData)

base, raw = blob_text()

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

# wrapper context: dump wide window and locate function entry heuristically
dump(0x5687C0, 0x568960, "unlink-caller wrapper around 0x5688EB", marks=(0x5688EB,))

# find callers of link 0x47E8A0
L.append("=== E8 callers of link 0x0047E8A0 ===")
cl = e8_callers(0x47E8A0)
for c in cl:
    L.append("  0x%08X" % c)
L.append("count=%d" % len(cl))

# guess wrapper entries: nearest preceding function starts found by padding scan
def func_start_hint(va, maxback=0x800):
    seg_lo = va - maxback
    o = va  # index into raw: va-base
    i = o - 1
    while i > o - maxback and i > 0:
        b = raw[i]
        if b in (0xC3, 0xC2):
            j = i + (3 if b == 0xC2 else 1)
            pad = 0
            while j < len(raw) and raw[j] in (0xCC, 0x90):
                pad += 1; j += 1
            if pad >= 2:
                return base + j
        i -= 1
    return None

# wrapper entry candidates from padding scan around 0x5688EB
L.append("")
L.append("=== padding-scan function starts between 0x568000 and 0x569000 ===")
starts = []
i = 0x568000 - base
while i < 0x569000 - base - 1:
    if raw[i] in (0xC3, 0xC2):
        j = i + (3 if raw[i] == 0xC2 else 1)
        pad = 0
        while raw[j] in (0xCC, 0x90):
            pad += 1; j += 1
        if pad >= 2:
            starts.append(base + j)
            i = j
            continue
    i += 1
for s in starts:
    L.append("  start 0x%08X" % s)

txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
