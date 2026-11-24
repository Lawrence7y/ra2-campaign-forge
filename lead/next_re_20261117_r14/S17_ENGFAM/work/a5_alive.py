# a-S17-ENGFAM audit, script a5: chain aliveness upward + IAT names + bounded data-ref rescan + helper 0x67FDD0
import pefile, capstone, struct, os, bisect
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM\EVIDENCE"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
d = bytes(pe.__data__)
def va2off(va): return pe.get_offset_from_rva(va - IB)
def read(va, n): return d[va2off(va):va2off(va)+n]
def dw(va): return struct.unpack("<I", read(va, 4))[0]

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
code = read(TEXT_LO, TEXT_HI-TEXT_LO)
call_sites = {}; jmp_sites = {}
for insn in md.disasm(code, TEXT_LO):
    if insn.mnemonic == ".byte": continue
    try: ops = list(insn.operands)
    except capstone.CsError: continue
    if insn.mnemonic == "call" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        call_sites.setdefault(ops[0].imm & 0xFFFFFFFF, []).append(insn.address)
    elif insn.mnemonic == "jmp" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        jmp_sites.setdefault(ops[0].imm & 0xFFFFFFFF, []).append(insn.address)

fstarts = sorted(set(call_sites.keys()))
def containing(addr):
    i = bisect.bisect_right(fstarts, addr) - 1
    return fstarts[i] if i >= 0 else None

# RTTI vtables (compact rebuild)
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
    return [(vt, td, funcs.index(fn), len(funcs)) for vt, (td, funcs) in sorted(vts.items()) if fn in funcs]

iat = {}
for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
    for imp in entry.imports:
        if imp.address:
            iat[imp.address] = (entry.dll.decode(), imp.name.decode() if imp.name else "ord%d" % imp.ordinal)

lines = []
for a in (0x7E11C4, 0x7E15C8, 0x7E15F4):
    lines.append("IAT[0x%08X] = %s" % (a, iat.get(a)))
lines.append("string @0x83D5C4 = %r" % read(0x83D5C4, 64))
lines.append("string @0x83D5C4 tail = %r" % read(0x83D5C4+64, 64))
lines.append("")

lines.append("== bounded .data dword refs to ENGFAM entries (raw-backed only [0x812000,0x87E000) + .rdata) ==")
ENTRIES = [0x0067FDF0 + 0x80*(n-1) for n in list(range(1,17))+list(range(18,36))] + [0x006805F0]
ESET = set(ENTRIES)
total = 0
for lo, hi in SCANS:
    buf = read(lo, hi-lo)
    for off in range(0, len(buf)-4, 4):
        v = struct.unpack_from("<I", buf, off)[0]
        if v in ESET:
            total += 1
            lines.append("  0x%08X (in %s) -> 0x%08X" % (lo+off, "rdata" if lo==0x7E1000 else "data", v))
lines.append("  bounded data refs total: %d" % total)
lines.append("")

lines.append("== upward chain from the 3 outer-callers ==")
frontier = [0x4C6CB0, 0x559C20, 0x55D360]
seen = set()
depth = 0
while frontier and depth < 5:
    nxt = []
    for fn in frontier:
        if fn in seen: continue
        seen.add(fn)
        cs = call_sites.get(fn, [])
        js = jmp_sites.get(fn, [])
        vt = vtable_of(fn)
        lines.append("fn 0x%08X: call_sites=%d %s | jmp=%d | vtable=%s" % (
            fn, len(cs), [hex(x) for x in cs][:12], len(js), vt if vt else "NONE"))
        for s in cs[:12]:
            c = containing(s)
            lines.append("    site 0x%08X in 0x%08X" % (s, c))
            if c: nxt.append(c)
        for s in js[:6]:
            c = containing(s)
            lines.append("    jmp-site 0x%08X in 0x%08X" % (s, c))
            if c: nxt.append(c)
    frontier = list(dict.fromkeys(nxt))[:16]
    depth += 1
lines.append("")

lines.append("== helper 0x67FDD0 body ==")
for insn in md.disasm(read(0x67FDD0, 0x20), 0x67FDD0):
    lines.append("  0x%08X  %-20s %s %s" % (insn.address, " ".join("%02X"%b for b in insn.bytes), insn.mnemonic, insn.op_str))
    if insn.mnemonic == "ret": break

with open(os.path.join(OUT, "alive.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
