# -*- coding: utf-8 -*-
"""W100 step6: allocator 0x7C8E17 callers; MapClass-global 0x87F7E8 refs; 0x8B413C writers.
Output -> EVIDENCE\\step6_alloc.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step6_alloc.txt"

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

def disasm_range(start, end, mark_lo=None, mark_hi=None):
    for ins in md.disasm(read(start, end - start), start):
        mark = "  <<" if (mark_lo is not None and mark_lo <= ins.address < mark_hi) else "    "
        print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

def find_calls(target):
    hits = []
    for i in range(len(text) - 5):
        if text[i] == 0xE8:
            rel = struct.unpack_from("<i", text, i + 1)[0]
            if TVA + i + 5 + rel == target:
                hits.append(TVA + i)
    return hits

print("=== 0x7C8E17 head (allocator?) ===")
disasm_range(0x007C8E17, 0x007C8E60)
print()

callers = find_calls(0x007C8E17)
print("=== callers of 0x7C8E17: %d ===" % len(callers))
# group: show context of each unique 'size computation' pattern:
# heuristic: disasm [c-0x30, c+2] from several start offsets to find best window
from collections import Counter
szpat = Counter()
for c in callers:
    # disasm starting at c-0x40 .. c, linear; collect last imul/lea/shl chain results
    win = md.disasm(read(c - 0x40, 0x42), c - 0x40)
    ins_list = list(win)
    tail = [i for i in ins_list if i.address + i.size <= c]
    ops = [i for i in tail if i.mnemonic in ("imul", "lea", "shl", "push")]
    desc = "; ".join("%s %s" % (i.mnemonic, i.op_str) for i in ops[-4:])
    szpat[desc] += 1
for desc, cnt in szpat.most_common(40):
    print("  x%-3d %s" % (cnt, desc))
print()

# show full windows for the most interesting ones (large multiplies)
print("=== windows of callers with 'imul' in tail ===")
shown = 0
for c in callers:
    win = list(md.disasm(read(c - 0x40, 0x42), c - 0x40))
    tail = [i for i in win if i.address + i.size <= c]
    if any(i.mnemonic == "imul" for i in tail) and shown < 10:
        shown += 1
        print("--- caller 0x%08X ---" % c)
        for i in tail[-12:]:
            print("  0x%08X: %-16s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        print()
print()

print("=== 0x578080 head (called with ecx=0x87F7E8) ===")
disasm_range(0x00578080, 0x005780E0)
print()

for tgt in (0x0087F7E8, 0x008B413C, 0x008B4148):
    pat = struct.pack("<I", tgt)
    sites = []
    i = 0
    while True:
        j = text.find(pat, i)
        if j < 0: break
        sites.append(TVA + j)
        i = j + 1
    print("=== refs to 0x%08X: %d ===" % (tgt, len(sites)))
    for s in sites[:12]:
        print("  0x%08X" % s)
    print()

# full window for first 4 refs to 0x87F7E8
pat = struct.pack("<I", 0x0087F7E8)
i = 0; cnt = 0
print("=== windows around first refs to 0x87F7E8 ===")
while cnt < 4:
    j = text.find(pat, i)
    if j < 0: break
    i = j + 1; cnt += 1
    va = TVA + j
    print("--- ref 0x%08X ---" % va)
    disasm_range(va - 0x20, va + 0x18)
    print()

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
