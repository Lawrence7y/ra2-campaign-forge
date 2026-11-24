# -*- coding: utf-8 -*-
"""W100 step5: enumerate refs to width globals 0x0089E864/0x0089E870/0x0089E7C0/0x0089C2DC;
raw-search sizeof candidates 0x140..0x180 as imul imm32.
Output -> EVIDENCE\\step5_width_refs.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step5_width_refs.txt"

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

TARGETS = [0x0089E864, 0x0089E870, 0x0089E7C0, 0x0089C2DC]
for tgt in TARGETS:
    pat = struct.pack("<I", tgt)
    sites = []
    i = 0
    while True:
        j = text.find(pat, i)
        if j < 0: break
        sites.append(TVA + j)
        i = j + 1
    print("=== refs to 0x%08X in .text: %d ===" % (tgt, len(sites)))
    for s in sites:
        # disasm a window starting 6 bytes before, and try to catch the instruction
        print("  ref at 0x%08X" % s)
    print()

# for each ref site, disassemble window [site-0x20, site+0x20] starting a few aligned
# points to get best decode; simplest: linear disasm from site-0x20
for tgt in TARGETS:
    pat = struct.pack("<I", tgt)
    print("########## windows around refs to 0x%08X ##########" % tgt)
    i = 0
    cnt = 0
    while cnt < 14:
        j = text.find(pat, i)
        if j < 0: break
        i = j + 1
        cnt += 1
        va = TVA + j
        print("--- ref 0x%08X ---" % va)
        start = va - 0x18
        code = read(start, 0x30)
        for ins in md.disasm(code, start):
            mark = "  <<" if ins.address <= va < ins.address + ins.size else "    "
            print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        print()
    if cnt == 14:
        print("  (window list truncated at 14 for 0x%08X)" % tgt)
    print()

# raw search: imul r32, r/m32, imm32 (69 /r) with imm in sizeof candidates
print("########## imul imm32 in [0x130..0x200] raw ##########")
for sz in range(0x130, 0x201, 4):
    pat = struct.pack("<I", sz)
    i = 0
    hits = []
    while True:
        j = text.find(pat, i)
        if j < 0: break
        i = j + 1
        # check byte 2 or 3 back is 0x69 or 0x6B (imm8 for sz<128 skipped)
        if j >= 2 and text[j-2] == 0x69:
            hits.append((TVA + j - 2, "69"))
        elif j >= 3 and text[j-3] == 0x69:  # modrm with sib/disp variants
            hits.append((TVA + j - 3, "69+"))
    if hits:
        print("  sizeof cand 0x%X: %d imul-imm hits: %s" % (sz, len(hits),
              ", ".join("0x%08X(%s)" % h for h in hits[:10])))

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
