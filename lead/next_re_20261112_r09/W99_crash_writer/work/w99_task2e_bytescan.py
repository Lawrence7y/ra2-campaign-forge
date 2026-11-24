# W99 Task2e: desync-immune byte-level scan for disp32 writes with disp==0xE4/0xE8,
# GetCellAt disasm (0x5657A0/0x565730) for sizeof(CellClass), and IsCellOccupied chain walk hunt.
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import disas, PE, IMAGEBASE

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W99_crash_writer\EVIDENCE\task2e_bytescan.txt"
L = []

with open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb") as f:
    blob = f.read()

L.append("=== byte-level scan: 89 /r (mov [reg+disp32], reg) and C7 /0 with disp32==0xE4 or 0xE8 ===")
def byte_scan(disp):
    hits = []
    d = struct.pack("<I", disp)
    for s in PE.sections:
        if s.Name.rstrip(b"\x00").decode() != ".text":
            continue
        base = IMAGEBASE + s.VirtualAddress
        raw = blob[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
        n = len(raw)
        i = 0
        while i < n - 6:
            b0 = raw[i]
            if b0 == 0x89 or b0 == 0x8B or b0 == 0xC7:
                m = raw[i+1]
                if 0x80 <= m <= 0xBF:
                    rm = m & 7
                    idx = i + 2
                    if rm == 4:  # SIB
                        if i + 6 < n and raw[idx+4:idx+8] == d:
                            hits.append((base + i, "SIB"))
                        i += 1
                    else:
                        if raw[idx:idx+4] == d:
                            hits.append((base + i, "noSIB"))
            i += 1
    return hits

for disp in (0xE4, 0xE8):
    L.append("-- disp 0x%X --" % disp)
    for va, kind in byte_scan(disp):
        b = blob[0]  # unused
        o = va - IMAGEBASE
        # fetch raw bytes at va via PE mapping later; simple print of opcode pair
        L.append("  0x%08X (%s) modrm=%02X" % (va, kind, 0))

L.append("")
L.append("=== decode each byte-scan hit with capstone (aligned at hit) ===")
import capstone
MD2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def off2va_fetch(va, n=10):
    for s in PE.sections:
        if s.Name.rstrip(b"\x00").decode() != ".text":
            continue
        if IMAGEBASE + s.VirtualAddress <= va < IMAGEBASE + s.VirtualAddress + s.SizeOfRawData:
            o = s.PointerToRawData + (va - IMAGEBASE - s.VirtualAddress)
            return blob[o:o+n]
    return None

for disp in (0xE4, 0xE8):
    L.append("-- disp 0x%X --" % disp)
    for va, kind in byte_scan(disp):
        b = off2va_fetch(va, 10)
        ins = list(MD2.disasm(b, va))
        if ins:
            i0 = ins[0]
            L.append("  0x%08X: %-18s %s %s" % (va, i0.bytes.hex().upper(), i0.mnemonic, i0.op_str))

L.append("")
L.append("=== add reg,0xE4 / lea reg,[reg+0xE4] byte scan (81 C?/8D with disp32 0xE4) ===")
pat_add = []
d = struct.pack("<I", 0xE4)
for s in PE.sections:
    if s.Name.rstrip(b"\x00").decode() != ".text":
        continue
    base = IMAGEBASE + s.VirtualAddress
    raw = blob[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
    i = 0
    while True:
        j = raw.find(bytes([0x81]) , i)  # too broad; instead find d preceded by 81 C0+C7
        break
    # do it properly: scan for disp32 0xE4 anywhere, then check preceding byte for 81/8D/SIB patterns
    j = 0
    cnt = 0
    while True:
        j = raw.find(d, j)
        if j < 0:
            break
        prev = raw[j-2:j]
        if prev[0] in (0x81,) and 0xC0 <= prev[1] <= 0xC7:
            L.append("  add-reg site 0x%08X: 81 %02X + disp 0xE4" % (base + j - 2, prev[1]))
            cnt += 1
        if prev[0] == 0x8D and (0x80 <= prev[1] <= 0xBF):
            L.append("  lea site 0x%08X: 8D %02X + disp 0xE4" % (base + j - 2, prev[1]))
            cnt += 1
        j += 1

L.append("")
L.append("=== GetCellAt 0x5657A0 (0x80 bytes) ===")
for va, bh, mn, ops, insn in disas(0x5657A0, 0x5657A0 + 0x80):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

L.append("")
L.append("=== 0x565730 variant (0x60 bytes) ===")
for va, bh, mn, ops, insn in disas(0x565730, 0x565730 + 0x60):
    L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

L.append("")
L.append("=== IsCellOccupied range 0x51C0D0..0x51C420: hunt chain walk (+0x30 / +0xE4 / +0x2C calls) ===")
for va, bh, mn, ops, insn in disas(0x51C0D0, 0x51C420):
    if ("+ 0x30]" in ops or "+ 0xe4]" in ops or "+ 0x2c]" in ops or mn == "call"):
        L.append("0x%08X: %-22s %s %s" % (va, bh, mn, ops))

txt = "\n".join(L) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
