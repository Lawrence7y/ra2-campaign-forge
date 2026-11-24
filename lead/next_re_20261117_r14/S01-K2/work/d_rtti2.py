#!/usr/bin/env python3
"""S01-K2: fixed RTTI scan (inline class-name strings) + GetSize slots + key fn dumps."""
import os, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
EV = os.path.join(ROOT, r"lead\next_re_20261117_r14\S01-K2\EVIDENCE")
IB = 0x400000
blob = open(EXE, "rb").read()
import pefile
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
    o = va2off(va); return blob[o:o+n] if o is not None else b""

def dword(va):
    b = read(va, 4); return struct.unpack("<I", b)[0] if len(b) == 4 else 0

def secname(va):
    for n, vs, vsz, pr, rs in secs:
        if vs <= va < vs + max(vsz, rs): return n
    return None

def in_sec(va, name): return secname(va) == name

def fmt(ins): return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}"

def dump(va, n, name):
    t = "\n".join(fmt(i) for i in md.disasm(read(va, n), va)) + "\n"
    open(os.path.join(EV, name), "w", encoding="utf-8").write(t)

# ---- RTTI: scan .rdata bytes for inline ".?AV"? name; TD = namepos-8 ----
rva_va = next(v for n, v, vsz, pr, rs in secs if n == ".rdata")
rva_sz = next(max(vsz, rs) for n, v, vsz, pr, rs in secs if n == ".rdata")
rdata = read(rva_va, rva_sz)
KEYS = ["logic", "winmain", "conquer", "mainloop", "game"]
found = []
for i in range(len(rdata) - 8):
    if rdata[i:i+4] in (b".?AV", b".?AU"):
        end = rdata.find(b"@@", i)
        if end < 0 or end - i > 120: continue
        nm = rdata[i:end+2]
        try: s = nm.decode("ascii")
        except: continue
        if any(k in s.lower() for k in KEYS):
            td = rva_va + i - 8
            found.append((td, s))
seen = set(); found = [(t,s) for t,s in found if not (t in seen or seen.add(t))]
print("=== RTTI TDs matching keys (name inline at TD+8) ===")
for td, s in found: print(f"  TD {td:#x} (vptr={dword(td):#x}) {s}")

# ---- For each TD: COL where COL+0xC==TD; vtable[-1]==COL ----
print("\n=== COL/vtable/GetSize chains ===")
out = []
for td, s in found:
    cols = []
    for p in range(rva_va, rva_va + rva_sz - 0x10, 4):
        if dword(p + 0xC) == td: cols.append(p)
    if not cols:
        out.append(f"TD {td:#x} {s}\n  NO COL found (COL+0xC==TD)"); continue
    for col in cols:
        vts = []
        for q in range(rva_va, rva_va + rva_sz - 8, 4):
            if dword(q) == col and in_sec(q + 4, ".rdata"): vts.append(q + 4)
        if not vts:
            out.append(f"TD {td:#x} {s}\n  COL {col:#x} but no vtable[-1]==COL"); continue
        for vt in vts:
            slots = [dword(vt + 4*i) for i in range(24)]
            gs = []
            for i, sv in enumerate(slots):
                if in_sec(sv, ".text") and read(sv, 1) == b"\xb8" and read(sv + 5, 1) == b"\xc3":
                    imm = struct.unpack("<I", read(sv + 1, 4))[0]
                    gs.append((i, sv, imm))
            line = f"TD {td:#x} {s}\n  COL {col:#x} vtable {vt:#x}\n  slots: " + " ".join(f"{x:08X}" for x in slots)
            line += "\n  B8-imm32-C3: " + (", ".join(f"v[{i}]={sv:#x} imm={imm}" for i,sv,imm in gs) if gs else "none")
            out.append(line)
            print("  " + line.replace("\n", "\n  "))
open(os.path.join(EV, "getsize_candidates.txt"), "w", encoding="utf-8").write("\n\n".join(out) + "\n")
if not found: print("  (none)")

# ---- dump key functions on the per-frame path ----
print("\n=== key fn dumps ===")
for va, n, name in [
    (0x5D4D50, 0x120, "fn_5D4D50_disasm.txt"),
    (0x55E160, 0x200, "fn_55E160_disasm.txt"),
    (0x69A300, 0x100, "fn_69A300_disasm.txt"),
    (0x48D080, 0x100, "fn_48D080_disasm.txt"),
    (0x683EB0, 0x100, "fn_683EB0_disasm.txt"),
]:
    dump(va, n, name); print(f"  {name} {va:#x}+{n:#x}")
print("DONE")
