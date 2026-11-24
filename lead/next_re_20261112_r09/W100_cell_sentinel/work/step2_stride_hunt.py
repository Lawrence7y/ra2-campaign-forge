# -*- coding: utf-8 -*-
"""W100 work script 2: hunt for CellClass stride & base.
1) full disasm of 0x51BF90, filter instructions touching 0xE4/0xE8/0x30/imul
2) disasm 0x484F20
3) imul immediate histogram over .text (stride candidates)
4) guard-pattern enumeration A0 A0 E9 A8 00
Output -> EVIDENCE\\step2_stride_hunt.txt
"""
import pefile, capstone, struct, collections

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step2_stride_hunt.txt"

import io, sys
buf = io.StringIO()
class Tee:
    def write(self, s):
        sys.__stdout__.write(s)
        buf.write(s)
    def flush(self):
        pass
sys.stdout = Tee()

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
_fh = open(EXE, "rb")
def read(va, n):
    off = pe.get_offset_from_rva(va - IB)
    _fh.seek(off)
    return _fh.read(n)

text_off = pe.get_offset_from_rva(0x1000)
f = open(EXE, "rb"); f.seek(text_off); text = f.read(0x3E0000); f.close()
TVA = 0x401000

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def disasm(va, n):
    return list(md.disasm(read(va, n), va))

print("=== 0x51BF90 full scan: instructions touching +0xE4/+0xE8/+0x30 or imul ===")
for ins in disasm(0x0051BF90, 0x900):
    if ("0xe4" in ins.op_str or "0xe8" in ins.op_str or
        ins.mnemonic == "imul" or "0x30]" in ins.op_str):
        print("0x%08X: %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("\n=== 0x484F20 (called at 0x51BFF2 with ecx=arg1) head 0x80 ===")
for ins in disasm(0x00484F20, 0x80):
    print("0x%08X: %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("\n=== imul imm histogram over .text (imm>=0x40) ===")
hist = collections.Counter()
for i in range(len(text) - 7):
    # imul r32, r/m32, imm32 : 69 /r id
    if text[i] == 0x69:
        modrm = text[i+1]
        mod = modrm >> 6
        if mod != 3:  # only count memory-form (rarely) and reg,reg forms both fine
            pass
        imm = struct.unpack_from("<i", text, i+2)[0] if True else 0
        # imm32 is at i+2 only if modrm has no extra bytes; approximate: just read next 4 bytes when reg,reg form (mod==3, /r reg field != 5 handled below)
        if mod == 3:
            imm = struct.unpack_from("<i", text, i+2)[0]
            if 0x40 <= imm <= 0x800:
                hist[imm] += 1
    # imul r32, r/m32, imm8 : 6B /r ib
    if text[i] == 0x6B:
        modrm = text[i+1]
        if (modrm >> 6) == 3:
            imm = struct.unpack_from("<b", text, i+2)[0]
            if 0x40 <= imm <= 0x7F:
                hist[imm] += 1
for imm, c in sorted(hist.items(), key=lambda kv: -kv[1])[:40]:
    print("  imm=0x%03X (%d) count=%d" % (imm, imm, c))

print("\n=== guard pattern 'A0 A0 E9 A8 00' sites in .text ===")
pat = bytes.fromhex("a0a0e9a800")
sites = []
i = 0
while True:
    j = text.find(pat, i)
    if j < 0: break
    sites.append(TVA + j)
    i = j + 1
print("count=%d" % len(sites))
print("first 30: " + ", ".join("0x%08X" % s for s in sites[:30]))

sys.stdout = sys.__stdout__
with open(OUT, "w", encoding="utf-8") as o:
    o.write(buf.getvalue())
print("saved -> " + OUT)
