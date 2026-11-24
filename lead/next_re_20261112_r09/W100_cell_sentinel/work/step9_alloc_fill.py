# -*- coding: utf-8 -*-
"""W100 step9: table allocation & fill; iterator 0x578290.
Output -> EVIDENCE\\step9_alloc_fill.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step9_alloc_fill.txt"

buf = io.StringIO()
class Tee:
    def write(self, s): sys.__stdout__.write(s); buf.write(s)
    def flush(self): pass
sys.stdout = Tee()

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
fh = open(EXE, "rb")
def read(va, n):
    fh.seek(pe.get_offset_from_rva(va - IB)); return fh.read(n)
fh.seek(pe.get_offset_from_rva(0x1000)); text = fh.read(0x3E0000)
TVA = 0x401000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def dump(start, end, label):
    print("--- %s ---" % label)
    for ins in md.disasm(read(start, end - start), start):
        print("0x%08X: %-16s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print()

# 1) find 'shl reg, 0xB' (C1 E? 0B) sites, check window +-0x40 for call 0x7C8E17 or +0x13C write
print("=== 'shl reg,0xB' sites with nearby 0x13C-member write or allocator call ===")
sites = []
i = 0
while True:
    j = text.find(b"\xc1\xe0\x0b", i)  # shl eax,0xB
    if j < 0: break
    sites.append(TVA + j)
    i = j + 1
for pat_shl in (b"\xc1\xe1\x0b", b"\xc1\xe2\x0b", b"\xc1\xe3\x0b", b"\xc1\xe5\x0b",
                b"\xc1\xe6\x0b", b"\xc1\xe7\x0b", b"\xc1\xef\x0b", b"\xc1\xee\x0b",
                b"\xc1\xed\x0b", b"\xc1\xec\x0b", b"\xc1\xeb\x0b", b"\xc1\xea\x0b"):
    i = 0
    while True:
        j = text.find(pat_shl, i)
        if j < 0: break
        sites.append(TVA + j)
        i = j + 1
print("total shl reg,0xB sites: %d" % len(sites))
interesting = []
for s in sites:
    lo = s - TVA - 0x60
    if lo < 0: continue
    win = text[lo:lo + 0xD0]
    if b"\xe8" in win and (struct.pack("<i", 0x007C8E17 - (s + 2)) in win or True):
        pass
    # simpler: scan instructions in window and look for '0x13c' op_str or call target 0x7c8e17
    try:
        ins_list = list(md.disasm(win, s - 0x60))
    except Exception:
        continue
    has_13c = any("+ 0x13c" in ins.op_str or "0x13c]" in ins.op_str for ins in ins_list)
    has_alloc = any(ins.mnemonic == "call" and ins.op_str.startswith("0x7c8e17") for ins in ins_list)
    if has_13c or has_alloc:
        interesting.append(s)
print("interesting: %d" % len(interesting))
for s in interesting[:6]:
    print("--- window around 0x%08X ---" % s)
    start = s - 0x70
    for ins in md.disasm(read(start, 0x100), start):
        mark = " <<" if ins.address <= s < ins.address + ins.size else "   "
        print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print()

# 2) all writes 'mov [reg+0x13C], r32' : 89 /r with mod=10, rm=reg, disp32=0x13C
print("=== mov [reg+0x13C], r32 sites (89 mod10) ===")
i = 0
hits = []
while i < len(text) - 6:
    if text[i] == 0x89 and 0x80 <= text[i+1] <= 0xBF:
        disp = struct.unpack_from("<i", text, i + 2)[0]
        if disp == 0x13C:
            hits.append(TVA + i)
    i += 1
print("count: %d" % len(hits))
for h in hits[:10]:
    print("--- writer 0x%08X ---" % h)
    start = h - 0x60
    for ins in md.disasm(read(start, 0x70), start):
        mark = " <<" if ins.address <= h < ins.address + ins.size else "   "
        print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print()

# 3) iterator 0x578290
dump(0x00578290, 0x00578330, "0x578290 iterator (returns next CellClass*)")

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
