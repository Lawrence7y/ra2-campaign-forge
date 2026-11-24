# -*- coding: utf-8 -*-
"""W100 step11: what happens with table[idx] in the slab loop; where does [esp+0x48] come from.
Output -> EVIDENCE\\step11_table_use.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step11_table_use.txt"

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
    for ins in md.disasm(read(start, end - start), start):
        print("0x%08X: %-16s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print()

dump(0x0056655D, 0x00566680, "0x56655D.. use of table[idx] in slab loop")
dump(0x00565D00, 0x00565E20, "0x565D00.. post-alloc trace ([esp+0x48] source?)")
dump(0x00566260, 0x00566440, "0x566260..0x566440 (other slab loop with add ebp,0x148)")

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
