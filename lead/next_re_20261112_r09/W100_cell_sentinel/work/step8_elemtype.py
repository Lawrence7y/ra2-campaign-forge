# -*- coding: utf-8 -*-
"""W100 step8: pin down element type of [0x87F924] table.
- 0x47B3A0 full-ish (receives element as ecx)
- writers of 0x87F924 (A3/89 24 F9 87 00)
- 0x578100 head (MapClass method touching +0x13C)
- containing function of 0x483B3B: find function start, dump head
Output -> EVIDENCE\\step8_elemtype.txt
"""
import pefile, capstone, struct, io, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W100_cell_sentinel\EVIDENCE\step8_elemtype.txt"

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

dump(0x0047B3A0, 0x0047B460, "0x47B3A0 (receives table element as ecx)")

# writers of 0x87F924: byte patterns '24 F9 87 00' preceded by A3 (mov [g],eax) or 89 modrm
pat = bytes.fromhex("24f98700")
i = 0
sites = []
while True:
    j = text.find(pat, i)
    if j < 0: break
    sites.append(TVA + j)
    i = j + 1
print("=== all '24 F9 87 00' occurrences: %d ===" % len(sites))
writers = []
for s in sites:
    prev = text[s - TVA - 1 + 0] if False else None
    b = text[s - TVA - 1]
    if b == 0xA3:  # mov [g], eax
        writers.append((s - 1, "mov [0x87F924], eax"))
    elif b in (0x89, 0x8B):
        # 89 /r -> reg to rm; check modrm byte after: at s is 24 F9 87 00? no: s points at '24'
        # encoding: 89 modrm(00 101 xxx? ) ... for [disp32]: 89 0D 24 F9 87 00 etc.
        pass
print("direct A3 writers:", ["0x%08X" % w for w, _ in writers])
print()
# show context for every A3 writer and for '89 ?? 24 F9 87 00'
for s in sites:
    b = text[s - TVA - 1]
    if b == 0xA3:
        va = TVA + s - 1
        print("--- writer 0x%08X (mov [0x87F924], eax) ---" % va)
        start = va - 0x50
        for ins in md.disasm(read(start, 0x56), start):
            mark = " <<" if ins.address <= va < ins.address + ins.size else "   "
            print("%s0x%08X: %-16s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        print()

# mov r32, [0x87F924] read via 8B 0D/15/... = find '8B ?? 24 F9 87 00' too many; skip
# C7 05 24 F9 87 00 imm32 (mov [g], imm)
pat2 = bytes.fromhex("c70524f98700")
i = 0
while True:
    j = text.find(pat2, i)
    if j < 0: break
    imm = struct.unpack_from("<I", text, j + 6)[0]
    print("C7 writer at 0x%08X: mov dword [0x87F924], 0x%08X" % (TVA + j, imm))
    i = j + 1

# also .data initial value of 0x87F924 itself
fh.seek(pe.get_offset_from_rva(0x87F924 - IB))
init = fh.read(4)
print(".data initial dword at 0x87F924: 0x%08X (raw %s)" % (struct.unpack("<I", init)[0], init.hex()))
fh.seek(pe.get_offset_from_rva(0x87F928 - IB))
init2 = fh.read(4)
print(".data initial dword at 0x87F928: 0x%08X" % struct.unpack("<I", init2)[0])
print()

dump(0x00578100, 0x00578200, "0x578100 (MapClass method touching +0x13C)")

# containing function of 0x483B3B: scan back for int3 padding (CC CC) or ret+90 alignment
addr = 0x00483B3B
scan = addr - 0x400
best = None
t = text
for k in range(addr - TVA - 1, addr - TVA - 0x800, -1):
    # function prologues commonly: 83 EC / 55 8B EC / push regs after CC padding
    if t[k] == 0xCC and t[k+1] != 0xCC:
        cand = TVA + k + 1
        if best is None or cand > best:
            best = cand
print("nearest function start (after CC padding) before 0x483B3B: 0x%08X" % (best or 0))
if best:
    dump(best, best + 0x60, "start of function containing 0x483B3B")
    dump(0x00483AF0, 0x00483B80, "0x483AF0..0x483B80 (the table-write sequence full)")

sys.stdout = sys.__stdout__
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("saved -> " + OUT)
