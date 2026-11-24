# -*- coding: utf-8 -*-
"""W100 step4: inspect imul sites -> derive CellClass base/stride formula.
Output -> EVIDENCE\\step4_imul_ctx.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step4_imul_ctx.txt"

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
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def dump(start, end, label):
    print("--- %s ---" % label)
    # back up 0x20 to land mid-instruction is risky; start at given point but note it
    for ins in md.disasm(read(start, end - start), start):
        print("0x%08X: %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

dump(0x0047D980, 0x0047DA10, "0x47D9C9 imul eax,[0x0089E7C0]")
dump(0x004804A0, 0x00480520, "0x4804DC imul eax,[0x0089E7C0]")
dump(0x00489F70, 0x0048A000, "0x489FB1 imul eax,[0x0089E870]")
dump(0x004D0CB0, 0x004D0D30, "0x4D0CED imul eax,[0x008B3D68]")
dump(0x00429BF0, 0x00429C60, "0x429C27 imul eax,[0x0089C2DC]")

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
