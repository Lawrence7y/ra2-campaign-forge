# a-S17-ENGFAM audit, script a4: chain identity + edx arg setup at 35 call sites + bodies of wrappers
import pefile, capstone, struct, os, bisect
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

def vtable_of(fn):
    out = []
    for vt, (td, funcs) in sorted(vts.items()):
        if fn in funcs:
            out.append((vt, td, funcs.index(fn), len(funcs)))
    return out

md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
code = read(TEXT_LO, TEXT_HI-TEXT_LO)
call_sites = {}
for insn in md.disasm(code, TEXT_LO):
    if insn.mnemonic == ".byte": continue
    try: ops = list(insn.operands)
    except capstone.CsError: continue
    if insn.mnemonic == "call" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        call_sites.setdefault(ops[0].imm & 0xFFFFFFFF, []).append(insn.address)

fstarts = sorted(set(call_sites.keys()))
def containing(addr):
    i = bisect.bisect_right(fstarts, addr) - 1
    return fstarts[i] if i >= 0 else None

lines = []
lines.append("== chain: who calls 0x67D300 ==")
site = call_sites.get(0x67D300, [])[0]
cont = containing(site)
lines.append("  site 0x%08X contained in 0x%08X" % (site, cont))
for vt, td, idx, n in vtable_of(cont):
    lines.append("    container 0x%08X IS vtable member: vt 0x%08X class=%s slot=%d/%d" % (cont, vt, td, idx, n))
lines.append("")
lines.append("== who calls 0x67CEF0 (outer) and their vtable identity ==")
for s in call_sites.get(0x67CEF0, []):
    c = containing(s)
    lines.append("  call@0x%08X in 0x%08X" % (s, c))
    for vt, td, idx, n in vtable_of(c):
        lines.append("    caller 0x%08X vtable: vt 0x%08X class=%s slot=%d/%d" % (c, vt, td, idx, n))
lines.append("")

# bodies: 0x67CEF0 (outer), and 0x67D300 head + around first/last block-call sites
lines.append("== disasm 0x67CEF0 (outer wrapper) ==")
for insn in md.disasm(read(0x67CEF0, 0x80), 0x67CEF0):
    lines.append("  0x%08X  %-20s %s %s" % (insn.address, " ".join("%02X"%b for b in insn.bytes), insn.mnemonic, insn.op_str))
    if insn.mnemonic == "ret": break
lines.append("")
lines.append("== disasm 0x67D300 head (0x60 bytes) ==")
for insn in md.disasm(read(0x67D300, 0x60), 0x67D300):
    lines.append("  0x%08X  %-20s %s %s" % (insn.address, " ".join("%02X"%b for b in insn.bytes), insn.mnemonic, insn.op_str))
lines.append("")
lines.append("== 0x67D300 around block call sites 0x67DEF0..0x67E3C0 (edx/ecx setup per call) ==")
start = 0x67DEF0
for insn in md.disasm(read(start, 0x67E3C0-start), start):
    mark = ""
    if insn.mnemonic == "call":
        ops = insn.operands
        if ops and ops[0].type == capstone.x86.X86_OP_IMM:
            t = ops[0].imm & 0xFFFFFFFF
            if 0x67FDF0 <= t <= 0x680F70:
                mark = "   ==> block call target 0x%08X" % t
    lines.append("  0x%08X  %-20s %s %s%s" % (insn.address, " ".join("%02X"%b for b in insn.bytes), insn.mnemonic, insn.op_str, mark))
lines.append("")
lines.append("== disasm 0x67D1AF container head: 0x%08X ==" % cont)
for insn in md.disasm(read(cont, 0x50), cont):
    lines.append("  0x%08X  %-20s %s %s" % (insn.address, " ".join("%02X"%b for b in insn.bytes), insn.mnemonic, insn.op_str))
lines.append("")

with open(os.path.join(OUT, "chain.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines[:40]))
print("...\nwrote chain.txt")
