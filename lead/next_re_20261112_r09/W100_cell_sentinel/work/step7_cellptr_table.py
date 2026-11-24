# -*- coding: utf-8 -*-
"""W100 step7: verify [0x87F924] elements are CellClass*; find writer; dump MapClass vtable.
Output -> EVIDENCE\\step7_cellptr_table.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step7_cellptr_table.txt"

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
fh.seek(pe.get_offset_from_rva(0x3E1000)); rdata = fh.read(0x31000)
TVA, RVA_, RD = 0x401000, 0x7E1000, 0x3E1000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def disasm_range(start, end):
    for ins in md.disasm(read(start, end - start), start):
        print("0x%08X: %-16s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("=== 0x578080 FULL (0x578080..0x578130) ===")
disasm_range(0x00578080, 0x00578130)
print()

def refs(target, blob, base_va):
    pat = struct.pack("<I", target)
    out = []
    i = 0
    while True:
        j = blob.find(pat, i)
        if j < 0: break
        out.append(base_va + j)
        i = j + 1
    return out

for tgt in (0x0087F924, 0x0087F928):
    sites = refs(tgt, text, TVA)
    print("=== .text refs to 0x%08X: %d ===" % (tgt, len(sites)))
    for s in sites:
        print("  0x%08X" % s)
    print()
    for s in sites[:6]:
        print("--- window 0x%08X ---" % s)
        start = s - 0x24
        for ins in md.disasm(read(start, 0x44), start):
            mark = " <<" if ins.address <= s < ins.address + ins.size else "   "
            print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        print()

print("=== vtable at 0x7E1964 (MapClass instance vtbl) slots 0..15 ===")
vt = 0x7E1964
off = vt - RVA_
for k in range(16):
    val = struct.unpack_from("<I", rdata, off + k*4)[0]
    print("  slot %2d (+0x%02X): 0x%08X" % (k, k*4, val))
print()

# what is at 0x00459EC0 (WhatAmI=6 impl per R09_COMMON) and 0x00523340 (WhatAmI=15)
for fn, lbl in ((0x00459EC0, "WhatAmI=6 impl?"), (0x00523340, "WhatAmI=15 impl?")):
    print("=== %s 0x%08X ===" % (lbl, fn))
    disasm_range(fn, fn + 0x10)
    print()

# Also: what about the 0x008B413C pointer array (IsCellOccupied's 0x484F20 lookup)?
# Its count 0x8B4148 - check refs windows at 0x00484ABE etc.
print("=== windows: writers/users of 0x8B413C & 0x8B4148 (first 4 each) ===")
for tgt in (0x008B413C, 0x008B4148):
    for s in refs(tgt, text, TVA)[:4]:
        print("--- ref 0x%08X (0x%08X) ---" % (s, tgt))
        start = s - 0x20
        for ins in md.disasm(read(start, 0x3C), start):
            mark = " <<" if ins.address <= s < ins.address + ins.size else "   "
            print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        print()

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
