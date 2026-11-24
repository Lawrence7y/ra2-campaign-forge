#!/usr/bin/env python3
"""W132c: name the vtables the CRT static init writes into the array globals.

W132b observed, in the static-init region:
    [0x00A8EB40] <- 0x007E9E24     then    [0x00A8EB40] <- 0x007E9E44
That is the classic two-step C++ construction: base ctor sets
`VectorClass<T>::vftable`, then the derived ctor overwrites it with
`DynamicVectorClass<T>::vftable`.  Together with
    [0x00A8EB54] <- 0x0000000A     (= base+0x14, CapacityIncrement = 10)
    [0x008B4114] <- 0x00000001     (= base+0x0C, IsInitialized   = true)
the object layout is pinned to the byte.

This script resolves each such vtable to its COL -> TypeDescriptor name, so the
element type of every array is stated by the binary itself, not by a header.
"""
import os
import struct

import pefile

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


TD = {}
FILE_SECTIONS = [s for s in SECS if s["name"] in (".rdata", ".data")]
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

# TD -> the VectorClass<X> names we care about
vec_td = {td: nm for td, nm in TD.items() if "VectorClass" in nm}
by_name = {}
for td, nm in vec_td.items():
    by_name[nm] = td

want = [
    ".?AV?$DynamicVectorClass@PAVBuildingClass@@@@",
    ".?AV?$VectorClass@PAVBuildingClass@@@@",
    ".?AV?$DynamicVectorClass@PAVUnitClass@@@@",
    ".?AV?$VectorClass@PAVUnitClass@@@@",
    ".?AV?$DynamicVectorClass@PAVHouseClass@@@@",
    ".?AV?$DynamicVectorClass@PAVInfantryClass@@@@",
    ".?AV?$DynamicVectorClass@PAVAircraftClass@@@@",
    ".?AV?$DynamicVectorClass@PAVAbstractClass@@@@",
    ".?AV?$DynamicVectorClass@PAVFootClass@@@@",
    ".?AV?$DynamicVectorClass@PAVTechnoClass@@@@",
    ".?AV?$DynamicVectorClass@PAVTriggerClass@@@@",
    ".?AV?$DynamicVectorClass@PAVParticleSystemClass@@@@",
]
print("=" * 100)
print("W132c-1  TypeDescriptor addresses for the arrays of interest")
print("=" * 100)
for w in want:
    print("   %-52s TD=%s" % (w, ("0x%08X" % by_name[w]) if w in by_name else "ABSENT"))

# COLs whose pTD is a VectorClass TD
COL = {}
for s in FILE_SECTIONS:
    lo, hi = s["va"], min(s["vend"], s["raw_end"])
    for col in range(lo, hi - 0x14, 4):
        ptd = u32(col + 0x0C)
        if ptd in vec_td:
            off = u32(col + 0x04)
            if off is not None and off < 0x10000:
                COL[col] = (off, ptd, vec_td[ptd])
print("\n   COLs typing a VectorClass instantiation: %d" % len(COL))

print()
print("=" * 100)
print("W132c-2  resolve each vtable the static init stores")
print("=" * 100)
STORES = [
    (0x004E6B7D, 0x00A8EB40, 0x007E9E24),
    (0x004E6BA8, 0x00A8EB40, 0x007E9E44),
    (0x004E6BFD, 0x00A8E390, 0x007E9E64),
    (0x004E6C28, 0x00A8E390, 0x007E9E84),
    (0x004E6C7D, 0x008B4108, 0x007E9EA4),
    (0x004E6CA8, 0x008B4108, 0x007E9EC4),
    (0x004E6CFD, 0x00A80228, 0x007E9EE4),
    (0x004E6D28, 0x00A80228, 0x007E9F04),
    (0x004E6D7D, 0x00A8E9A8, 0x007E9F24),
    (0x004E6DA8, 0x00A8E9A8, 0x007E9F44),
]
for at, dst, vt in STORES:
    prev = u32(vt - 4)
    nm = COL.get(prev, (None, None, None))[2] if prev else None
    print("   @0x%08X  [0x%08X] <- vt 0x%08X   vtable[-1]=COL 0x%08X  -> %s"
          % (at, dst, vt, prev or 0, nm or "(no COL)"))

# Brute force: find the COL/VT pair for any VectorClass TD
print()
print("=" * 100)
print("W132c-3  locate vtable for each VectorClass COL by scanning for the COL pointer")
print("=" * 100)
bycol = {}
for s in FILE_SECTIONS:
    lo, hi = s["va"], min(s["vend"], s["raw_end"])
    raw = bytes(img[lo - IB: hi - IB])
    for col in COL:
        pat = struct.pack("<I", col)
        i = raw.find(pat)
        while i >= 0:
            va = lo + i
            vts = va + 4
            f0 = u32(vts)
            if f0 is not None and 0x401000 <= f0 < 0x7E038D:
                bycol.setdefault(col, []).append(vts)
            i = raw.find(pat, i + 1)

for w in want:
    td = by_name.get(w)
    if td is None:
        print("   %-52s TD absent" % w)
        continue
    cols = [c for c, (o, t, n) in COL.items() if t == td]
    vts = []
    for c in cols:
        vts.extend(bycol.get(c, []))
    print("   %-52s COL=%s VT=%s"
          % (w,
             ("0x%08X" % cols[0]) if cols else "none",
             ", ".join("0x%08X" % v for v in sorted(vts)[:4]) or "none"))
