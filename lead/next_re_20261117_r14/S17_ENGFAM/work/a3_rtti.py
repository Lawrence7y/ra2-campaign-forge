# a-S17-ENGFAM audit, script a3 (v2): RTTI over .data+.rdata + caller chain of 0x67D300/0x67CEF0
import pefile, capstone, struct, os, bisect
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM\EVIDENCE"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
d = bytes(pe.__data__)
def va2off(va): return pe.get_offset_from_rva(va - IB)
def read(va, n):
    off = va2off(va)
    return d[off:off+n]
def dw(va): return struct.unpack("<I", read(va, 4))[0]

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
# raw-backed regions only: .rdata [0x7E1000,0x811074) ; .data raw-backed [0x812000,0x87E000)
SCANS = [(0x7E1000, 0x811074, "rdata"), (0x812000, 0x87E000, "data")]

tds = {}
for lo, hi, tag in SCANS:
    buf = read(lo, hi - lo)
    i = 0
    while True:
        i = buf.find(b".?A", i)
        if i < 0: break
        end = buf.find(b"\x00", i)
        name = buf[i:end].decode(errors="replace")
        td_va = lo + i - 8
        if td_va >= lo:
            tds[td_va] = name
        i += 3
print("type descriptors found:", len(tds))

cols = {}
for lo, hi, tag in SCANS:
    buf = read(lo, hi - lo)
    for off in range(0, len(buf)-0x10, 4):
        sig = struct.unpack_from("<I", buf, off)[0]
        td = struct.unpack_from("<I", buf, off+0xC)[0]
        if sig == 0 and td in tds:
            cols[lo + off] = td
print("COL candidates:", len(cols))

vts = {}
for lo, hi, tag in SCANS:
    buf = read(lo, hi - lo)
    for off in range(4, len(buf)-4, 4):
        p = lo + off
        if dw(p-4) in cols:
            funcs = []
            q = p
            while True:
                try: v = dw(q)
                except Exception: break
                if TEXT_LO <= v < TEXT_HI:
                    funcs.append(v); q += 4
                else:
                    break
            if len(funcs) >= 2:
                vts[p] = (tds[cols[dw(p-4)]], funcs)
print("vtables found:", len(vts))

TARGET = set([0x0067D300, 0x0067CEF0] + [0x0067FDF0 + 0x80*(n-1) for n in list(range(1,17))+list(range(18,36))] + [0x006805F0])
lines = []
lines.append("== vtables containing any target (0x67D300 caller / 0x67CEF0 outer / 34 ENGFAM entries / gap slot) ==")
for vt, (td, funcs) in sorted(vts.items()):
    m = [f for f in funcs if f in TARGET]
    if m:
        lines.append("vtable 0x%08X class=%s slots=%d contains: %s at slot idx %s" % (
            vt, td, len(funcs), [hex(x) for x in m], [funcs.index(x) for x in m]))
lines.append("")
lines.append("== which classes own 0x67D300 (Save_Core) ==")
for vt, (td, funcs) in sorted(vts.items()):
    if 0x67D300 in funcs:
        lines.append("  vt 0x%08X class=%s slot=%d/%d" % (vt, td, funcs.index(0x67D300), len(funcs)))
lines.append("== which classes own 0x67CEF0 ==")
for vt, (td, funcs) in sorted(vts.items()):
    if 0x67CEF0 in funcs:
        lines.append("  vt 0x%08X class=%s slot=%d/%d" % (vt, td, funcs.index(0x67CEF0), len(funcs)))
lines.append("== which classes own any ENGFAM entry (expect none) ==")
own = 0
for vt, (td, funcs) in sorted(vts.items()):
    m = [f for f in funcs if TEXT_LO <= f < TEXT_HI and (0x67FDF0 <= f <= 0x680F70)]
    if m:
        own += len(m)
        lines.append("  vt 0x%08X class=%s contains %s" % (vt, td, [hex(x) for x in m]))
lines.append("  total ENGFAM-range vtable entries: %d" % own)
lines.append("")

# save element-side RTTI candidates: classes whose name contains PersistStream pattern? Just dump TD names containing 'Persist'
lines.append("== TD names containing 'Persist' ==")
for td, name in sorted(tds.items()):
    if "Persist" in name:
        lines.append("  TD 0x%08X %s" % (td, name))
lines.append("")

with open(os.path.join(OUT, "rtti.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("vtable matches written; ENGFAM-range vtable entries:", own)

# ---------- caller chain sweep ----------
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
code = read(TEXT_LO, TEXT_HI - TEXT_LO)
call_sites = {}; jmp_sites = {}
for insn in md.disasm(code, TEXT_LO):
    if insn.mnemonic == ".byte": continue
    try: ops = list(insn.operands)
    except capstone.CsError: continue
    if insn.mnemonic == "call" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        call_sites.setdefault(ops[0].imm & 0xFFFFFFFF, []).append(insn.address)
    elif insn.mnemonic == "jmp" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        jmp_sites.setdefault(ops[0].imm & 0xFFFFFFFF, []).append(insn.address)

fstarts = sorted(set(list(call_sites.keys()) + [0x67D300, 0x67CEF0, 0x67D1AF]))
def containing(addr):
    i = bisect.bisect_right(fstarts, addr) - 1
    return fstarts[i] if i >= 0 else None

for fn in (0x67D300, 0x67CEF0):
    c = call_sites.get(fn, []); j = jmp_sites.get(fn, [])
    print("0x%08X: %d call sites %s | %d jmp %s" % (fn, len(c), [hex(x) for x in c], len(j), [hex(x) for x in j]))
    for s in c: print("   call@0x%08X in 0x%08X" % (s, containing(s)))
    for s in j: print("   jmp@0x%08X in 0x%08X" % (s, containing(s)))

with open(os.path.join(OUT, "rtti.txt"), "a", encoding="utf-8") as f:
    f.write("== callers of 0x67D300 / 0x67CEF0 ==\n")
    for fn in (0x67D300, 0x67CEF0):
        c = call_sites.get(fn, []); j = jmp_sites.get(fn, [])
        f.write("0x%08X call_sites=%s jmp_sites=%s\n" % (fn, [hex(x) for x in c], [hex(x) for x in j]))
        for s in c + j:
            f.write("   site@0x%08X contained in 0x%08X\n" % (s, containing(s)))
