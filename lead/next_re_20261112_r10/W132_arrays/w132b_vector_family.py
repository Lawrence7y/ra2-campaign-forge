#!/usr/bin/env python3
"""W132b: derive the engine's per-type object-array table from the IMAGE,
and cross-check the community YRpp header against it.

Layout (YRpp ArrayClasses.h, confirmed arithmetically below):
    VectorClass<T>            +0x00 vftable
                              +0x04 T* Items
                              +0x08 int Capacity
                              +0x0C bool IsInitialized
                              +0x0D bool IsAllocated
    DynamicVectorClass<T>     +0x10 int Count
                              +0x14 int CapacityIncrement

So for a declared array base B: Items = B+4, Count = B+0x10.

This script does NOT trust YRpp. It:
  1. scans .rdata for MSVC TypeDescriptors (name at TD+8) and prints every
     VectorClass / DynamicVectorClass instantiation it finds;
  2. resolves COL -> TD so a vtable can be named;
  3. disassembles the CRT static-initialiser region and reports every store of
     a .rdata vtable pointer into a .data global, naming the COL it points at.
     Those stores are the binary's own statement of "this global IS a
     DynamicVectorClass<T*>";
  4. cross-checks every YRpp-declared base against the observed B+4 / B+0x10
     access pairs found in .text.

Read-only over the file.
"""
import bisect
import os
import struct
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
SECS = []
for s in pe.sections:
    SECS.append({"name": s.Name.rstrip(b"\x00").decode("latin-1"),
                 "va": IB + s.VirtualAddress,
                 "vend": IB + s.VirtualAddress + s.Misc_VirtualSize,
                 "raw_end": IB + s.VirtualAddress + s.SizeOfRawData})
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D


def blk(va):
    for s in SECS:
        if s["va"] <= va < s["vend"]:
            return s
    return None


def sec_of(va):
    s = blk(va)
    return s["name"] if s else None


def has_bytes(va, n=4):
    s = blk(va)
    return bool(s) and (va + n) <= s["raw_end"]


def u32(va):
    if not has_bytes(va):
        return None
    return struct.unpack("<I", img[va - IB: va - IB + 4])[0]


def cstr(va, cap=240):
    if not has_bytes(va, 1):
        return None
    i = va - IB
    out = bytearray()
    while i < len(img) and len(out) < cap:
        c = img[i]
        if c == 0:
            break
        if not (32 <= c < 127):
            return None
        out.append(c)
        i += 1
    return out.decode("latin-1")


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# ------------------------------------------------------------------ 1. TDs
# NOTE: this image keeps its RTTI strings in .data (0x815DE8+), not .rdata,
# so scan every file-backed section. pVFTable of a TD points at the *type_info
# vftable*, which lives in .rdata.
FILE_SECTIONS = [s for s in SECS if s["name"] in (".rdata", ".data")]
TD = {}                                   # td_va -> name
COL = {}                                  # col_va -> (offset, td, name)
for s in FILE_SECTIONS:
    lo, hi = s["va"], min(s["vend"], s["raw_end"])
    raw = bytes(img[lo - IB: hi - IB])
    i = raw.find(b".?A")
    while i >= 0:
        va = lo + i
        nm = cstr(va)
        if nm and (nm.startswith(".?AV") or nm.startswith(".?AU")):
            td = va - 8
            pv = u32(td)
            if pv is not None and sec_of(pv) == ".rdata":
                TD[td] = nm
        i = raw.find(b".?A", i + 1)

print("=" * 104)
print("W132b-1  TypeDescriptors parsed from .rdata: %d" % len(TD))
vecs = {td: nm for td, nm in TD.items() if "VectorClass" in nm}
print("         of which Vector/DynamicVector instantiations: %d" % len(vecs))
for td, nm in sorted(vecs.items(), key=lambda t: t[1]):
    print("   TD 0x%08X  %s" % (td, nm))

# --------------------------------------------------------------- 2. COL -> TD
for s in FILE_SECTIONS:
    lo, hi = s["va"], min(s["vend"], s["raw_end"])
    for col in range(lo, hi - 0x14, 4):
        ptd = u32(col + 0x0C)
        if ptd in TD:
            off = u32(col + 0x04)
            if off is not None and off < 0x10000:
                COL[col] = (off, ptd, TD[ptd])
print("\n         COLs resolved (pTD known, offset sane): %d" % len(COL))


def name_vtable(vt):
    """vtable[-1] holds the COL; return the class name."""
    if not (0x00800000 <= vt < 0x00C00000):
        return None, None
    col = u32(vt - 4)
    if col in COL:
        off, td, nm = COL[col]
        return nm, col
    return None, col


# ------------------------------------------------------- 3. static init scan
print()
print("=" * 104)
print("W132b-2  stores of a vtable pointer into a .data global (CRT static init)")
print("=" * 104)


def ops(insn):
    """capstone raises on .operands for skipdata pseudo-instructions."""
    if insn.id == 0:
        return None
    try:
        return insn.operands
    except Exception:
        return None


def scan_vptr_stores(lo, hi):
    win = bytes(img[lo - IB: hi - IB])
    out = []
    for insn in md.disasm(win, lo):
        o = ops(insn)
        if not o:
            continue
        # form A: mov dword ptr [g], imm32
        if (insn.mnemonic == "mov" and len(o) == 2
                and o[0].type == X86_OP_MEM
                and o[1].type == X86_OP_IMM):
            m = o[0].mem
            if m.base == 0 and m.index == 0:
                dst = m.disp & 0xFFFFFFFF
                val = o[1].imm & 0xFFFFFFFF
                if sec_of(dst) in (".data", ".bss"):
                    nm, col = name_vtable(val)
                    out.append((insn.address, dst, val, nm, col))
    return out


for label, lo, hi in (("init region 0x4E6A00-0x4E6E00", 0x004E6A00, 0x004E6E00),):
    rows = scan_vptr_stores(lo, hi)
    print("\n-- %s : %d vtable-into-.data stores" % (label, len(rows)))
    for at, dst, val, nm, col in rows:
        print("   store 0x%08X  [0x%08X] <- 0x%08X  COL 0x%08X  %s"
              % (at, dst, val, col or 0, nm))

# --------------------------------------------------- 4. YRpp cross-check table
YRPP = [
    ("CommandClass*", 0x87F658), ("LightConvertClass*", 0x87F698),
    ("IsometricTileClass*", 0x87F750), ("VoxelAnimClass*", 0x887388),
    ("AlphaShapeClass*", 0x88A0F0), ("CaptureManagerClass*", 0x89E0F0),
    ("ConvertClass*", 0x89ECF8), ("DiskLaserClass*", 0x8A0208),
    ("EBolt*", 0x8A0E88), ("EMPulseClass*", 0x8A3870),
    ("FootClass*", 0x8B3DC0), ("TeamClass*", 0x8B40E8),
    ("UnitClass*", 0x8B4108), ("BuildingLightClass*", 0x8B4190),
    ("ParticleSystemClass*", 0xA80208), ("HouseClass*", 0xA80228),
    ("SuperClass*", 0xA83CB8), ("ParticleClass*", 0xA83DC8),
    ("InfantryClass*", 0xA83DE8), ("FactoryClass*", 0xA83E30),
    ("SmudgeClass*", 0xA8B1E0), ("AircraftClass*", 0xA8E390),
    ("AbstractTypeClass*", 0xA8E968), ("TerrainClass*", 0xA8E988),
    ("AnimClass*", 0xA8E9A8), ("TriggerClass*", 0xA8EAE8),
    ("TechnoTypeClass*", 0xA8EB00), ("BuildingClass*", 0xA8EB40),
    ("WaveClass*", 0xA8EC38), ("OverlayClass*", 0xA8EC50),
    ("TechnoClass*", 0xA8EC78), ("IsometricTileTypeClass*", 0xA8ED28),
    ("BulletClass*", 0xA8ED40), ("IonBlastClass*", 0xAA0118),
    ("LineTrail*", 0xABCB78), ("SpotlightClass*", 0xAC1678),
    ("ParasiteClass*", 0xAC4910), ("RadBeam*", 0xB04A60),
    ("RadSiteClass*", 0xB04BD0), ("ColorScheme*", 0xB054D0),
    ("SlaveManagerClass*", 0xB0B5F0), ("SpawnManagerClass*", 0xB0B880),
    ("TActionClass*", 0xB0E658), ("TagClass*", 0xB0E720),
    ("TemporalClass*", 0xB0EC60), ("TEventClass*", 0xB0F1A0),
    ("AbstractClass*", 0xB0F720), ("VocClass*", 0xB1D378),
    ("VoxClass*", 0xB1D4A0),
]

text_off = TEXT_LO - IB
text = bytes(img[text_off: TEXT_HI - IB])


def n_hits(va):
    pat = struct.pack("<I", va)
    n, i = 0, text.find(pat)
    while i >= 0:
        n += 1
        i = text.find(pat, i + 1)
    return n


print()
print("=" * 104)
print("W132b-3  YRpp-declared instance arrays vs the observed B+4 / B+0x10 access pair")
print("=" * 104)
print("%-22s %-10s %-8s %-8s %-8s %s" % ("element type", "base", "+4(Items)", "+0x10(Cnt)", "base", "verdict"))


def real_refs(va):
    """number of instructions that really reference [va] (validated via disasm)."""
    pat = struct.pack("<I", va)
    hits, i = [], text.find(pat)
    while i >= 0:
        hits.append(TEXT_LO + i)
        i = text.find(pat, i + 1)
    ok = []
    for h in hits:
        lo = max(TEXT_LO, h - 16)
        win = bytes(img[lo - IB: min(TEXT_HI, h + 17) - IB])
        hit = False
        for insn in md.disasm(win, lo):
            if insn.address + insn.size <= h:
                continue
            if insn.address > h:
                break
            for op in (ops(insn) or []):
                if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
                        and (op.mem.disp & 0xFFFFFFFF) == va:
                    hit = True
                    break
            if hit:
                break
        if hit:
            ok.append(h)
    return ok


RESULT = []
for typ, base in YRPP:
    a_items = real_refs(base + 4)
    a_cnt = real_refs(base + 0x10)
    a_base = real_refs(base)
    ok = (len(a_items) > 0 and len(a_cnt) > 0)
    RESULT.append((typ, base, len(a_items), len(a_cnt), len(a_base), ok))
    print("%-22s 0x%08X %-8d %-8d %-8d %s"
          % (typ, base, len(a_items), len(a_cnt), len(a_base),
             "PAIR OK" if ok else ("no pair" if not a_items and not a_cnt else "partial")))

good = sum(1 for r in RESULT if r[5])
print("\n  B+4 and B+0x10 both referenced: %d / %d" % (good, len(RESULT)))

print()
print("=" * 104)
print("W132b-4  what the ledger §853-3 globals actually are (computed from the table)")
print("=" * 104)
probe = [("DAT_00a8eaf8", 0x00A8EAF8), ("DAT_00a8eb44", 0x00A8EB44),
         ("DAT_00a8eb50", 0x00A8EB50), ("DAT_008b3dd0", 0x008B3DD0),
         ("DAT_00a8ec88", 0x00A8EC88), ("DAT_00a80218", 0x00A80218),
         ("DAT_00a83df8", 0x00A83DF8), ("DAT_00a8022c", 0x00A8022C),
         ("unit_items", 0x008B410C), ("unit_count", 0x008B4118)]
for nm, va in probe:
    hit = None
    for typ, base in YRPP:
        if va == base + 4:
            hit = "%s :: Items" % typ
        elif va == base + 0x10:
            hit = "%s :: Count" % typ
        elif va == base:
            hit = "%s :: vptr" % typ
    print("   %-14s 0x%08X -> %s" % (nm, va, hit or "NOT in the YRpp array table"))
