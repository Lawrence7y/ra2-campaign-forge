# -*- coding: utf-8 -*-
"""W100 step3: find CellClass stride/base via imul-with-mem forms + chain-head context.
Output -> EVIDENCE\\step3_base_hunt.txt
"""
import pefile, capstone, struct, collections, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step3_base_hunt.txt"

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

def dis(va, n):
    return list(md.disasm(read(va, n), va))

def dump(va, n, label):
    print("--- %s ---" % label)
    for ins in dis(va, n):
        print("0x%08X: %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# A) chain-head context in IsCellOccupied
dump(0x0051C1C0, 0xE0, "0x51C1C0..0x51C2A0 chain-head context")

# B) proper imul histogram: 69 /r imm32 (all mod), 6B /r imm8 (all mod)
hist = collections.Counter(); locs = collections.defaultdict(list)
i = 0
n = len(text)
while i < n - 11:
    op = text[i]
    if op == 0x69 or op == 0x6B:
        modrm = text[i+1]; mod = modrm >> 6; rm = modrm & 7
        if op == 0x69:
            if mod == 3: l = 2
            elif mod == 1: l = 3
            elif mod == 2: l = 6
            else: l = 2 if rm == 5 else 2  # mod0: rm=5 needs disp32 -> imm after disp
            if mod == 0 and rm == 5:
                i += 1; continue
            immoff = i + 1 + l
        else:
            if mod == 3: immoff = i + 2
            elif mod == 1: immoff = i + 3
            elif mod == 2: immoff = i + 6
            else:
                i += 1; continue
        if immoff + 4 <= n:
            if op == 0x69:
                imm = struct.unpack_from("<i", text, immoff)[0]
            else:
                imm = struct.unpack_from("<b", text, immoff)[0]
            if 0x40 <= abs(imm) <= 0x400:
                hist[imm] += 1
                locs[imm].append(TVA + i)
    elif op == 0x0F and text[i+1] == 0xAF and text[i+2] == 0x05:
        tgt = struct.unpack_from("<I", text, i+3)[0]
        hist[("imul_eax_mem", tgt)] += 1
        locs[("imul_eax_mem", tgt)].append(TVA + i)
    i += 1

print("\n=== imul imm histogram (all forms, 0x40<=|imm|<=0x400) ===")
for k, c in sorted(hist.items(), key=lambda kv: -kv[1])[:30]:
    if isinstance(k, tuple):
        print("  imul eax,[0x%08X]  count=%d  sites=%s" % (k[1], c,
              ", ".join("0x%08X" % s for s in locs[k][:8])))
    else:
        print("  imm=0x%03X(%d) count=%d sites=%s" % (k, k, c,
              ", ".join("0x%08X" % s for s in locs[k][:8])))

# C) imul eax, dword [imm32] full list
print("\n=== '0F AF 05' imul eax,[imm32] sites ===")
i = 0
while True:
    j = text.find(b"\x0f\xaf\x05", i)
    if j < 0: break
    tgt = struct.unpack_from("<I", text, j+3)[0]
    print("  0x%08X: imul eax, [0x%08X]" % (TVA + j, tgt))
    i = j + 1

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
