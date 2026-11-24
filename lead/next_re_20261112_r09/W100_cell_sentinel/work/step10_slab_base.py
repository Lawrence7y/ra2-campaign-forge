# -*- coding: utf-8 -*-
"""W100 step10: locate runtime home of the CellClass slab base.
Dump 0x566460..0x566560 (loop head) and the function prologue search around 0x565D08.
Output -> EVIDENCE\\step10_slab_base.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step10_slab_base.txt"

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

dump(0x00566440, 0x00566560, "slab-init loop head 0x566440..0x566560 (ebp init?)")

# find function start of the container of 0x565D08: scan back for 'CC CC' or ret+nop run
addr = 0x00565D08
lo = addr - TVA
start = None
for k in range(lo - 1, lo - 0x3000, -1):
    if text[k] == 0xCC and text[k-1] == 0xCC:
        start = TVA + k + 2 if text[k+1] == 0xCC else TVA + k + 1
        break
print("container function start guess: 0x%08X" % (start or 0))
if start:
    dump(start, start + 0x50, "container prologue")

# also: search whole .text for 'add ebp,0x148' / 'add esi,0x148' etc: 81 C5/ C6/ C7/ C3/ C1 48 01 00 00
print("=== 'add reg, 0x148' (81 /r 48 01 00 00) sites ===")
i = 0
sites = []
while i < len(text) - 6:
    if text[i] == 0x81 and 0xC0 <= text[i+1] <= 0xC7:
        if struct.unpack_from("<I", text, i+2)[0] == 0x148:
            sites.append((TVA + i, "add %s, 0x148" % ["eax","ecx","edx","ebx","esp","ebp","esi","edi"][text[i+1]-0xC0]))
    i += 1
for s, d in sites:
    print("  0x%08X: %s" % (s, d))
print()
for s, d in sites[:8]:
    start = s - 0x50
    print("--- window 0x%08X ---" % s)
    for ins in md.disasm(read(start, 0x60), start):
        mark = " <<" if ins.address <= s < ins.address + ins.size else "   "
        print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print()

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
