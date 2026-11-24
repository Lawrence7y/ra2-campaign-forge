# a-S17-ENGFAM audit, script a7: ctor writes to each of the 35 vector globals -> vtable -> RTTI element name
import pefile, capstone, struct, os
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM\EVIDENCE"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
d = bytes(pe.__data__)
def va2off(va): return pe.get_offset_from_rva(va - IB)
def read(va, n): return d[va2off(va):va2off(va)+n]
def dw(va): return struct.unpack("<I", read(va, 4))[0]

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True

VECTORS = []
NAMES = {}
for n in list(range(1,17))+list(range(18,36)):
    va = 0x0067FDF0 + 0x80*(n-1)
    # edx value per block from a4 (call sites): build map here
VECTORS = {
 1:0xA83E30, 2:0xA8EB28, 3:0x887388, 4:0x8874C0, 5:0x887568, 6:0xA83D98, 7:0xA83DC8,
 8:0xA83D68, 9:0xA80208, 10:0xA83C80, 11:0xA8ED40, 12:0xB72608, 13:0xA8EC18, 14:0xA83D80,
 15:0xABCA10, 16:0x8B4190, 17:0x8B4120, 18:0xB0F4E8, 19:0x8A3870, 20:0xA8E330, 21:0xA83CB8,
 22:0xA8E318, 23:0xA8E988, 24:0x8B3D10, 25:0x88A0F0, 26:0xA8EC38, 27:0x89E0F0, 28:0x8A0208,
 29:0xAC4910, 30:0xB0EC60, 31:0x889FB8, 32:0xB0B880, 33:0xB0B5F0, 34:0x89C668, 35:0xB04BD0,
}
for k, v in VECTORS.items():
    NAMES[v] = "block#%02d" % k

SCANS = [(0x7E1000, 0x811074), (0x812000, 0x87E000)]
tds = {}
for lo, hi in SCANS:
    buf = read(lo, hi-lo); i = 0
    while True:
        i = buf.find(b".?A", i)
        if i < 0: break
        end = buf.find(b"\x00", i)
        tds[lo+i-8] = buf[i:end].decode(errors="replace"); i += 3
cols = {}
for lo, hi in SCANS:
    buf = read(lo, hi-lo)
    for off in range(0, len(buf)-0x10, 4):
        if struct.unpack_from("<I", buf, off)[0] == 0 and struct.unpack_from("<I", buf, off+0xC)[0] in tds:
            cols[lo+off] = struct.unpack_from("<I", buf, off+0xC)[0]
vts = {}
for lo, hi in SCANS:
    buf = read(lo, hi-lo)
    for off in range(4, len(buf)-4, 4):
        p = lo+off
        if dw(p-4) in cols:
            funcs = []; q = p
            while True:
                try: v = dw(q)
                except Exception: break
                if TEXT_LO <= v < TEXT_HI: funcs.append(v); q += 4
                else: break
            if len(funcs) >= 2: vts[p] = (tds[cols[dw(p-4)]], funcs)

VSET = set(VECTORS.values())
disp_hits = {}   # vec -> [(site, mnem, opstr, write?, imm)]
for insn in md.disasm(read(TEXT_LO, TEXT_HI-TEXT_LO), TEXT_LO):
    if insn.mnemonic == ".byte": continue
    try: ops = list(insn.operands)
    except capstone.CsError: continue
    for op in ops:
        if op.type == capstone.x86.X86_OP_MEM:
            disp = op.mem.disp & 0xFFFFFFFF
            if disp in VSET:
                immv = None
                for op2 in ops:
                    if op2.type == capstone.x86.X86_OP_IMM:
                        immv = op2.imm & 0xFFFFFFFF
                disp_hits.setdefault(disp, []).append((insn.address, insn.mnemonic, insn.op_str,
                                                       insn.mnemonic.startswith("mov") and op.access & 2, immv))

lines = []
for vec in sorted(VECTORS.values()):
    k = NAMES[vec]
    lines.append("== %s vector 0x%08X ==" % (k, vec))
    for site, mn, ops, isw, immv in disp_hits.get(vec, []):
        mark = ""
        if isw and immv is not None:
            if immv in vts:
                mark = "  <== VT 0x%08X class=%s" % (immv, vts[immv][0])
            else:
                mark = "  (imm 0x%08X not a found vtable)" % immv
        lines.append("  0x%08X %s %s%s" % (site, mn, ops, mark))
    lines.append("")

with open(os.path.join(OUT, "ctors.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote ctors.txt")
# quick console summary of verdict-relevant lines
for ln in lines:
    if "VT 0x" in ln or "== " in ln:
        print(ln)
