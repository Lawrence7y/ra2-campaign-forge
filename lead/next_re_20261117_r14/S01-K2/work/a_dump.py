#!/usr/bin/env python3
"""S01-K2 T2/T3 raw dump. Self-contained; read-only on gamemd.exe."""
import os, re, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

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
        if vs <= va < vs + max(vsz, rs):
            return pr + (rva - (vs - IB))
    raise ValueError(hex(va))

def read(va, n):
    o = va2off(va); return blob[o:o+n]

def dis(va, n):
    return list(md.disasm(read(va, n), va))

def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}"

def dump(va, n, name):
    t = "\n".join(fmt(i) for i in dis(va, n)) + "\n"
    with open(os.path.join(EV, name), "w", encoding="utf-8") as f: f.write(t)
    return len(t.splitlines())

def text_range():
    for n, vs, vsz, pr, rs in secs:
        if n == ".text": return vs, min(vsz, rs)
    return secs[0][1], min(secs[0][2], secs[0][4])

def sweep_rel32(target):
    vs, sz = text_range(); hits = []
    for ins in dis(vs, sz):
        if ins.mnemonic in ("call", "jmp") and ins.operands and ins.operands[0].type == CS_OP_IMM:
            if ins.operands[0].imm == target:
                hits.append((ins.address, ins.mnemonic))
    return hits

def sweep_abs_disp(addr):
    """instructions referencing absolute disp addr as mem operand (base=idx=0)."""
    vs, sz = text_range(); hits = []
    for ins in dis(vs, sz):
        for op in ins.operands:
            if op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp == addr:
                hits.append((ins.address, ins.mnemonic, ins.op_str)); break
    return hits

REGIONS = [
    ("crt_startup",       0x7CD7E0, 0x120),
    ("entry_6BB9A0",      0x6BB9A0, 0x500),
    ("mainloop",          0x48CCC0, 0x320),
    ("mainloop_inner",    0x48CE40, 0x90),
    ("perframe_55D360",   0x55D360, 0x400),
    ("framepred_55CFD0",  0x55CFD0, 0x200),
    ("gate_4DA560",       0x4DA540, 0x1A0),
    ("loco_4DA820",       0x4DA840, 0x100),
    ("layer_6D8DB0",      0x6D8DB0, 0x180),
    ("iter_6D97D0",       0x6D97D0, 0xC0),
    ("iter_6D9920",       0x6D9920, 0xC0),
    ("iter_6D9A50",       0x6D9A50, 0x100),
    ("draw_6D2790",       0x6D2790, 0x120),
    ("frameinc_55DE60",   0x55DE60, 0x40),
]
print("=== region dumps ===")
for name, va, n in REGIONS:
    c = dump(va, n, name + "_disasm.txt")
    print(f"  {name:<20} {va:#x}+{n:#x}  {c} insns")

print("\n=== direct call/jmp targets in MAINLOOP [0x48CCC0,0x48CFE0) ===")
for site, mn, tgt in [(i.address, i.mnemonic, i.operands[0].imm)
                      for i in dis(0x48CCC0, 0x320)
                      if i.mnemonic in ("call", "jmp") and i.operands and i.operands[0].type == CS_OP_IMM]:
    print(f"  {site:#x} {mn:<4} -> {tgt:#x}")

for t, label in [(0x48CCC0, "mainloop"), (0x55D360, "perframe"), (0x6D8DB0, "layerwalk")]:
    h = sweep_rel32(t)
    with open(os.path.join(EV, f"callers_{label}.txt"), "w", encoding="utf-8") as f:
        for a, m in h: f.write(f"{a:08X} {m}\n")
    print(f"\ncallers of {label} {t:#x}: {len(h)}")
    for a, m in h[:40]: print(f"  {a:#x} {m}")

for t, label in [(0xA8ED84, "frame_A8ED84"), (0xA8B238, "mode_A8B238"), (0xA8ED50, "bullets_A8ED50")]:
    h = sweep_abs_disp(t)
    with open(os.path.join(EV, f"xref_{label}.txt"), "w", encoding="utf-8") as f:
        for a, m, o in h: f.write(f"{a:08X} {m} {o}\n")
    print(f"\nxref abs[{t:#x}] {label}: {len(h)}")
    for a, m, o in h[:60]: print(f"  {a:#x} {m} {o}")

# IAT time functions
pe2 = pefile.PE(EXE); pe2.parse_data_directories()
print("\n=== IAT timer/window entries ===")
with open(os.path.join(EV, "iat_timers.txt"), "w", encoding="utf-8") as f:
    for entry in getattr(pe2, "DIRECTORY_ENTRY_IMPORT", []):
        dll = entry.dll.decode(errors="replace")
        for imp in entry.imports:
            nm = (imp.name or b"").decode(errors="replace")
            if re.search(r"(timeGetTime|QueryPerformance|GetTickCount|timeBeginPeriod|Sleep|GetForegroundWindow|IsIconic|ShowWindow|SetForegroundWindow|GetFocus|WM_)", nm, re.I):
                line = f"{dll}  {nm}  IAT@{imp.address:#x}"
                print("  " + line); f.write(line + "\n")
print("\nDONE")
