#!/usr/bin/env python3
"""S01-K2: timer call sites, mode writes, RTTI/GetSize for LogicClass & entry classes."""
import os, re, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM

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
    return None

def read(va, n):
    o = va2off(va)
    return blob[o:o+n] if o is not None else b""

def dword(va):
    b = read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else 0

def secname(va):
    for n, vs, vsz, pr, rs in secs:
        if vs <= va < vs + max(vsz, rs): return n
    return None

def in_sec(va, name):
    return secname(va) == name

# ---------- 1) timer IAT references ----------
vs, sz = next((v, min(vsz, rs)) for n, v, vsz, pr, rs in secs if n == ".text")
TIAT = {0x7E11F0: "Sleep", 0x7E1530: "timeGetTime", 0x7E11D0: "GetCurrentThreadId"}
sites = {k: [] for k in TIAT}
for ins in md.disasm(read(vs, sz), vs):
    if ins.id == 0: continue
    for op in ins.operands:
        if op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in TIAT:
            sites[op.mem.disp].append((ins.address, ins.mnemonic, ins.op_str)); break
print("=== timer IAT references ===")
with open(os.path.join(EV, "timer_iat_sites.txt"), "w", encoding="utf-8") as f:
    for a in sorted(TIAT):
        ss = sites[a]
        f.write(f"\n## {TIAT[a]} [{a:#x}] count={len(ss)}\n")
        for s, mn, ops in ss: f.write(f"{s:08X} {mn} {ops}\n")
        print(f"  {TIAT[a]:<20} count={len(ss)}")
        for s, mn, ops in ss[:15]: print(f"     {s:#x} {mn} {ops}")

# ---------- 2) mode writes from xref file ----------
xr = os.path.join(EV, "xref_all.txt")
txt = open(xr, encoding="utf-8").read()
m = re.search(r"## mode \[0xa8b238\].*?(?=\n## |\Z)", txt, re.S)
print("\n=== mode [0xa8b238] WRITE sites ===")
mode_w = []
if m:
    for line in m.group(0).splitlines():
        if re.match(r"^[0-9A-F]{8} W ", line):
            mode_w.append(line)
            print("  " + line)
with open(os.path.join(EV, "mode_writes.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(mode_w) + f"\n# total {len(mode_w)}\n")

# ---------- 3) RTTI TypeDescriptors matching target class names ----------
rdata_va = next((v for n, v, vsz, pr, rs in secs if n == ".rdata"), None)
rdata_size = next((max(vsz, rs) for n, v, vsz, pr, rs in secs if n == ".rdata"), 0)
rdata_end = rdata_va + rdata_size
def cstr(va, maxn=128):
    b = read(va, maxn)
    if not b: return ""
    z = b.find(b"\0")
    if z < 0: return ""
    try: return b[:z].decode("ascii")
    except: return ""

KEYS = ["Logic", "WinMain", "Game", "Conquer", "MainLoop"]
tds = []
for p in range(rdata_va, rdata_end - 8, 4):
    td = dword(p)
    if not in_sec(td, ".rdata"): continue
    nm = cstr(td + 8)
    if nm.startswith(".?AV") or nm.startswith(".?AU"):
        if any(k.lower() in nm.lower() for k in KEYS):
            tds.append((td, nm))
seen = set(); tds2 = []
for td, nm in tds:
    if td not in seen: seen.add(td); tds2.append((td, nm))
print("\n=== RTTI TypeDescriptors matching keys ===")
for td, nm in tds2: print(f"  TD {td:#x}  {nm}")
with open(os.path.join(EV, "rtti_targets.txt"), "w", encoding="utf-8") as f:
    for td, nm in tds2: f.write(f"{td:08X}\t{nm}\n")

# ---------- 4) COL (COL+0xC -> TD) and vtable[-1] -> COL, dump slots ----------
print("\n=== vtable / GetSize candidates from RTTI chain ===")
out = []
for td, nm in tds2:
    cols = []
    for p in range(rdata_va, rdata_end - 0x10, 4):
        if dword(p + 0xC) == td: cols.append(p)
    for col in cols:
        vts = []
        for q in range(rdata_va, rdata_end - 8, 4):
            if dword(q) == col and in_sec(q + 4, ".rdata"): vts.append(q + 4)
        for vt in vts:
            slots = [dword(vt + 4*i) for i in range(20)]
            gs = []
            for i, s in enumerate(slots):
                if in_sec(s, ".text") and read(s, 1) == b"\xb8" and read(s+5, 1) == b"\xc3":
                    imm = struct.unpack("<I", read(s+1, 4))[0]
                    gs.append((i, s, imm))
            line = f"TD {td:#x} {nm}\n  COL {col:#x} vtable {vt:#x}\n  slots[0..19]: " + " ".join(f"{x:08X}" for x in slots)
            line += "\n  B8-imm32-C3 slots: " + (", ".join(f"v[{i}]={s:#x} imm={imm:#x}({imm})" for i,s,imm in gs) if gs else "none")
            out.append(line)
            print("  " + line.replace("\n", "\n  "))
with open(os.path.join(EV, "getsize_candidates.txt"), "w", encoding="utf-8") as f:
    f.write("\n\n".join(out) + "\n")
print("DONE")
