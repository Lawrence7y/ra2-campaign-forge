#!/usr/bin/env python3
"""S01-K2 T3/T4: IAT resolution + single-pass absolute-xref (with R/W) + extra dumps."""
import os, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, CS_AC_READ, CS_AC_WRITE

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S01-K2")
EV = os.path.join(CARD, "EVIDENCE")
IB = 0x400000
blob = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)
secs = [(s.Name.rstrip(b"\0").decode(errors="replace"), IB + s.VirtualAddress,
         s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

def va2off(va):
    rva = va - IB
    for n, vs, vsz, pr, rs in secs:
        if vs <= va < vs + max(vsz, rs): return pr + (rva - (vs - IB))
    raise ValueError(hex(va))

def read(va, n):
    o = va2off(va); return blob[o:o+n]

def dis(va, n): return list(md.disasm(read(va, n), va))

def fmt(i): return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}"

def dump(va, n, name):
    t = "\n".join(fmt(i) for i in dis(va, n)) + "\n"
    open(os.path.join(EV, name), "w", encoding="utf-8").write(t)

# ---------- 1) IAT map ----------
pe2 = pefile.PE(EXE); pe2.parse_data_directories()
iat = {}
for entry in getattr(pe2, "DIRECTORY_ENTRY_IMPORT", []):
    dll = entry.dll.decode(errors="replace")
    for imp in entry.imports:
        nm = (imp.name or b"").decode(errors="replace") if imp.name else f"ord#{imp.ordinal}"
        iat[imp.address] = f"{dll}::{nm}"
with open(os.path.join(EV, "iat_full_map.txt"), "w", encoding="utf-8") as f:
    for a in sorted(iat): f.write(f"{a:08X}\t{iat[a]}\n")
print("=== IAT lookups (key slots) ===")
for a in [0x7e11f0, 0x7e1530, 0x7e11d0, 0x7e11f4, 0x7e1248, 0x7e1200, 0x7e1448,
          0x7e1480, 0x7e14d0, 0x7e1498, 0x7e1208, 0x7e120c, 0x7e1300, 0x7e124c]:
    print(f"  {a:#x} -> {iat.get(a,'?')}")

# ---------- 2) single-pass xref ----------
TARGETS = {
    0xA8ED84: "frame", 0xA8B238: "mode", 0xA8ED50: "bullets", 0xB0F730: "objects",
    0xA83D48: "focus_a83d48", 0xA83D49: "focus_a83d49", 0xA8ECD0: "flag_a8ecd0",
    0x8B41C0: "flag_8b41c0", 0xA8ED80: "flag_a8ed80", 0xA8E9A0: "flag_a8e9a0",
    0xA8B23C: "mode_aux_a8b23c", 0xA8B24C: "mode_aux_a8b24c", 0xA8E2E4: "limit_a8e2e4",
    0xA8B558: "a8b558", 0xA8B550: "a8b550", 0xA8D5F8: "a8d5f8", 0x8871E0: "pRules_8871e0",
}
vs, sz = next((v, min(vsz, rs)) for n, v, vsz, pr, rs in secs if n == ".text")
hits = {k: [] for k in TARGETS}
nins = 0
for ins in md.disasm(read(vs, sz), vs):
    nins += 1
    if ins.id == 0:  # skipdata synthetic .byte instruction: operands invalid
        continue
    for op in ins.operands:
        if op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in TARGETS:
            acc = "W" if (op.access & CS_AC_WRITE) else ("R" if (op.access & CS_AC_READ) else "?")
            hits[op.mem.disp].append((ins.address, acc, ins.mnemonic, ins.op_str))
            break
print(f"\n=== single-pass xref over {nins} insns ===")
with open(os.path.join(EV, "xref_all.txt"), "w", encoding="utf-8") as f:
    for a in sorted(TARGETS):
        hs = hits[a]
        w = sum(1 for h in hs if h[1] in ("W", "?"))
        f.write(f"\n## {TARGETS[a]} [{a:#x}]  total={len(hs)} write-ish={w}\n")
        for site, acc, mn, ops in hs:
            f.write(f"{site:08X} {acc} {mn} {ops}\n")
        print(f"  {TARGETS[a]:<18} [{a:#x}] total={len(hs):<5} write-ish={w}")

# ---------- 3) extra dumps ----------
DUMPS = [
    (0x55D700, 0x180, "perframe_tail_disasm.txt"),
    (0x48C8B0, 0x600, "framedraw_48C8B0_disasm.txt"),
    (0x69BAB0, 0x100, "fn_69BAB0_disasm.txt"),
    (0x69BB40, 0x100, "fn_69BB40_disasm.txt"),
    (0x7241A0, 0x100, "fn_7241A0_disasm.txt"),
    (0x72DFB0, 0x100, "fn_72DFB0_disasm.txt"),
    (0x48E0B0, 0x100, "fn_48E0B0_disasm.txt"),
    (0x55CFD0, 0x500, "framepred_full_disasm.txt"),
]
print("\n=== extra dumps ===")
for va, n, name in DUMPS:
    dump(va, n, name); print(f"  {name} {va:#x}+{n:#x}")
print("DONE")
