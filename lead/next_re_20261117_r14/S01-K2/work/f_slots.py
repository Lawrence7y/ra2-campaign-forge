#!/usr/bin/env python3
"""S01-K2: dump LogicClass vtable slots + getsize byte patterns + allocation points."""
import os, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_REG

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
EV = os.path.join(ROOT, r"lead\next_re_20261117_r14\S01-K2\EVIDENCE")
IB = 0x400000
blob = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

def va2off(va):
    try: return pe.get_offset_from_rva(va - IB)
    except: return None
def read(va, n):
    o = va2off(va); return blob[o:o+n] if o is not None else b""
def dword(va):
    b = read(va, 4); return struct.unpack("<I", b)[0] if len(b) == 4 else 0
def fmt(i): return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}"

print("=== LogicClass vtable 0x7E1900 slots ===")
vt = 0x7E1900
slots = []
for i in range(20):
    s = dword(vt + 4*i)
    slots.append(s)
    bs = read(s, 10).hex() if va2off(s) is not None else "??"
    # disassemble first 6 insns
    ds = " | ".join(fmt(x) for x in list(md.disasm(read(s, 24), s))[:5])
    print(f"  v[{i:2}] = {s:#010x}  bytes={bs:<20} {ds}")
    if i >= 14: break

print("\n=== byte pattern of GetSize candidates (v12=0x40CF30, v10=0x55B880) ===")
for s in [0x40CF30, 0x55B880, 0x7FA9A0]:
    print(f"  {s:#x}: {read(s,16).hex()}")
    for x in list(md.disasm(read(s, 32), s))[:8]: print("     "+fmt(x))

# ---- find operator new: scan imports for 'operator new' / malloc names, or find call sites with push big imm ----
pe2 = pefile.PE(EXE); pe2.parse_data_directories()
print("\n=== IAT malloc/new-ish ===")
newish = {}
for entry in getattr(pe2, "DIRECTORY_ENTRY_IMPORT", []):
    dll = entry.dll.decode(errors="replace")
    for imp in entry.imports:
        nm = (imp.name or b"").decode(errors="replace") if imp.name else f"ord#{imp.ordinal}"
        if re.search(r"(malloc|calloc|new|HeapAlloc|GlobalAlloc|LocalAlloc)", nm, re.I):
            newish[imp.address] = f"{dll}::{nm}"
            print(f"  {imp.address:#x} {dll}::{nm}")

# ---- find all 'push imm32 ; call <known operator new>' by locating operator new from the blitter factory 0x48EBF0 ----
# First find what 0x48EBF0 calls right after a push
print("\n=== 0x48EBF0 first 40 insns (blitter factory, to identify operator new) ===")
for x in list(md.disasm(read(0x48EBF0, 0x100), 0x48EBF0))[:40]: print("  "+fmt(x))
