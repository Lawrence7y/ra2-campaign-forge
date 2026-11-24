# W99 Task3: (1) redo SIB-form disp32 scan correctly (disp at i+3 for rm==4)
#            (2) full disasm 0x47E7E0..0x47E960 (link fn) and 0x47EA60..0x47EBB0 (unlink fn) with func starts
#            (3) E8 callers of unlink 0x47EA90 and link entry (auto-detected after dump)
#            (4) 0x47BC82 function start + vtable id of 0x7E4EEC (0x47BBA7 dtor's class) + slot11 of that vtable
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import disas, dword, PE, IMAGEBASE

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task3_link_unlink.txt"
L = []

with open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb") as f:
    blob = f.read()

def sect_raw(name=".text"):
    for s in PE.sections:
        if s.Name.rstrip(b"\x00").decode() == name:
            return IMAGEBASE + s.VirtualAddress, blob[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
    return None, None

base, raw = sect_raw()
d4 = struct.pack("<I", 0xE4)
d8 = struct.pack("<I", 0xE8)

L.append("=== SIB-form scan (89/C7/8B modrm rm=100, disp32==0xE4/0xE8 at i+3) ===")
import capstone
MD2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for tag, d in (("0xE4", d4), ("0xE8", d8)):
    L.append("-- disp %s --" % tag)
    n = len(raw)
    i = 0
    while i < n - 7:
        b0 = raw[i]
        if b0 in (0x89, 0x8B, 0xC7):
            m = raw[i+1]
            if 0x80 <= m <= 0xBF and (m & 7) == 4:
                if raw[i+3:i+7] == d:
                    va = base + i
                    ins = list(MD2.disasm(blob[s.PointerToRawData if False else 0:0] or b"", 0)) # placeholder
                    # fetch bytes
                    o = i
                    seg = raw[o:o+10]
                    try:
                        ins = list(MD2.disasm(seg, va))
                        i0 = ins[0]
                        L.append("  0x%08X: %-20s %s %s" % (va, i0.bytes.hex().upper(), i0.mnemonic, i0.op_str))
                    except Exception as e:
                        L.append("  0x%08X <err %s>" % (va, e))
        i += 1

L.append("")
L.append("=== link fn disasm 0x47E7E0..0x47E960 ===")
for va, bh, mn, ops, insn in disas(0x47E7E0, 0x47E960):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

L.append("")
L.append("=== unlink fn tail 0x47EAF0..0x47EBB0 (after WhatAmI call) ===")
for va, bh, mn, ops, insn in disas(0x47EAF0, 0x47EBB0):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

# caller scan helper
def e8_callers(target):
    res = []
    pat_ok = []
    i = 0
    n = len(raw)
    while i < n - 5:
        if raw[i] == 0xE8:
            rel = struct.unpack("<i", raw[i+1:i+5])[0]
            if base + i + 5 + rel == target:
                res.append(base + i)
        i += 1
    return res

L.append("")
L.append("=== direct E8 callers of unlink 0x0047EA90 ===")
for c in e8_callers(0x47EA90):
    L.append("  0x%08X" % c)

L.append("")
L.append("=== direct E8 callers of 0x0047BC82-region function (scan target 0x47BC30 guess below) ===")
# We don't know exact entry yet; dump region first then scan plausible starts
L.append("(deferred)")

L.append("")
L.append("=== 0x47BC82 function start hunt: disasm 0x47BBE0..0x47BCA0 ===")
for va, bh, mn, ops, insn in disas(0x47BBE0, 0x47BCA0):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

L.append("")
L.append("=== vtable 0x7E4EEC (dtor class at 0x47BB60) slot11 ===")
val, b = dword(0x7E4EEC + 0x2C)
L.append("[0x7E4EEC+0x2C] = 0x%08X" % val)
try:
    for va, bh, mn, ops, insn in disas(val, val + 8)[:2]:
        L.append("    0x%08X: %-14s %s %s" % (va, bh, mn, ops))
except Exception as e:
    L.append("    <err %s>" % e)

txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
