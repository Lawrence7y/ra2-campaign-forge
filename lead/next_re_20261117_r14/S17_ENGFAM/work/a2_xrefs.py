# a-S17-ENGFAM audit, script a2: own xref sweep + IAT resolve + IID bytes + caller containment
import pefile, capstone, struct, os
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM\EVIDENCE"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
d = pe.__data__

def rva2off(rva): return pe.get_offset_from_rva(rva)
def va2off(va): return rva2off(va - IB)
def read(va, n):
    off = va2off(va)
    return bytes(d[off:off+n])

ENTRIES = {}
for n in list(range(1,17))+list(range(18,36)):
    ENTRIES[0x0067FDF0 + 0x80*(n-1)] = "Save_VectorBlock_%02d" % n
ENTRIES[0x006805F0] = "slot#17(gap; Save_Sides per atlas name)"

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

# ---------- 1. linear sweep of .text: call/jmp/imm-refs ----------
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
code = read(TEXT_LO, TEXT_HI - TEXT_LO)
call_sites = {}   # target -> [site...]
jmp_sites = {}
starts = set()
data_refs = {}
for insn in md.disasm(code, TEXT_LO):
    starts.add(insn.address) if False else None
    if insn.mnemonic == ".byte":
        continue
    try:
        ops = list(insn.operands)
    except capstone.CsError:
        continue
    if insn.mnemonic in ("call",):
        op = ops[0] if ops else None
        if op is not None and op.type == capstone.x86.X86_OP_IMM:
            t = op.imm & 0xFFFFFFFF
            call_sites.setdefault(t, []).append(insn.address)
    elif insn.mnemonic == "jmp":
        op = ops[0] if ops else None
        if op is not None and op.type == capstone.x86.X86_OP_IMM:
            t = op.imm & 0xFFFFFFFF
            jmp_sites.setdefault(t, []).append(insn.address)
    for op in ops:
        if op.type == capstone.x86.X86_OP_IMM:
            v = op.imm & 0xFFFFFFFF
            if v in ENTRIES and not (TEXT_LO <= v < TEXT_HI):
                pass
            if v in ENTRIES:
                data_refs.setdefault(v, []).append((insn.address, insn.mnemonic, insn.op_str))

# ---------- 2. data dwords across .rdata/.data/.detour pointing at entries (vtable-like) ----------
def scan_dwords(lo, hi):
    found = {}
    off0 = va2off(lo)
    n = hi - lo
    raw = d[off0:off0+n]
    for i in range(0, min(n-4, len(raw)-4), 4):
        v = struct.unpack_from("<I", raw, i)[0]
        if v in ENTRIES:
            found.setdefault(v, []).append(lo + i)
    return found

rdata_lo, rdata_hi = 0x7E1000, 0x811074
data_lo, data_hi = 0x812000, 0xB79BE4
det_lo, det_hi = 0xB93000, 0xB95718
vref = {}
for lo, hi in ((rdata_lo, rdata_hi), (data_lo, data_hi), (det_lo, det_hi)):
    for k, vs in scan_dwords(lo, hi).items():
        vref.setdefault(k, []).extend(("0x%08X" % a) for a in vs)

# ---------- 3. IAT resolution of 0x7E15F4 ----------
iat_target = {}
for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
    dll = entry.dll.decode()
    for imp in entry.imports:
        if imp.address:
            iat_target[imp.address] = (dll, imp.name.decode() if imp.name else ("ord%d" % imp.ordinal))
print("IAT[0x7E15F4] =", iat_target.get(0x7E15F4, "NOT AN IMPORT"))

# ---------- 4. IID bytes at 0x7F7C80 ----------
iid = read(0x7F7C80, 16)
d1 = struct.unpack_from("<I", iid, 0)[0]
d2 = struct.unpack_from("<H", iid, 4)[0]
d3 = struct.unpack_from("<H", iid, 6)[0]
print("IID@0x7F7C80 = {%08X-%04X-%04X-%s-%s}" % (d1, d2, d3, iid[8:10].hex().upper(), iid[10:16].hex().upper()))

# ---------- 5. function-start map & caller containment ----------
fstarts = sorted(set(list(call_sites.keys()) + [e for e in ENTRIES] + list(jmp_sites.keys())))
import bisect
def containing(addr):
    i = bisect.bisect_right(fstarts, addr) - 1
    return fstarts[i] if i >= 0 else None

lines = []
for va, name in sorted(ENTRIES.items()):
    cs = call_sites.get(va, [])
    js = jmp_sites.get(va, [])
    vr = vref.get(va, [])
    lines.append("%-24s 0x%08X direct_call_sites=%d %s | jmp_sites=%d %s | data_refs=%s" % (
        name, va, len(cs), [hex(x) for x in cs], len(js), [hex(x) for x in js], vr[:8]))
    for s in cs:
        c = containing(s)
        lines.append("    call@0x%08X -> contained in 0x%08X" % (s, c) if c else "    call@0x%08X -> no container" % s)

with open(os.path.join(OUT, "xrefs.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))



