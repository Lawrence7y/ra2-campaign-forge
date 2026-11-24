#!/usr/bin/env python3
"""W132d: the engine's complete instance-array table, NAMED BY THE BINARY.

Method (all evidence inside gamemd.exe):
  Every static instance array is a `DynamicVectorClass<T*>` global.  It gets a
  `.CRT$XCU` initialiser of the canonical shape

      xor  eax,eax
      push <atexit handler>
      mov  [B+4],  eax          ; Items      = 0
      mov  [B+8],  eax          ; Capacity   = 0
      mov  byte [B+0xC], 1      ; IsInitialized = true
      mov  byte [B+0xD], al     ; IsAllocated  = false
      mov  [B+0],  <vftable>    ; vptr -> DynamicVectorClass<T*>::vftable
      mov  [B+0x14], 0xA        ; CapacityIncrement = 10
      mov  [B+0x10], eax        ; Count = 0
      call atexit
      ret

  so scanning .text for `mov dword ptr [B], imm32` with imm32 a .rdata pointer
  and then resolving  vftable[-1] -> COL -> TypeDescriptor -> mangled name
  names the element type from the binary's own RTTI, with no header involved.

Output: instance_arrays.tsv   (element, base, items, count, vtable, col, td,
                               n_items_refs, n_count_refs, yrpp_agrees)
"""
import os
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D

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


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True


def ops(insn):
    if insn.id == 0:
        return None
    try:
        return insn.operands
    except Exception:
        return None


FILE_SECTIONS = [s for s in SECS if s["name"] in (".rdata", ".data")]
TD = {}
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

text = bytes(img[TEXT_LO - IB: TEXT_HI - IB])


def refs(va):
    """real instruction addresses whose memory operand is exactly [va]"""
    pat = struct.pack("<I", va)
    hits, i = [], text.find(pat)
    while i >= 0:
        hits.append(TEXT_LO + i)
        i = text.find(pat, i + 1)
    ok = []
    for h in hits:
        lo = max(TEXT_LO, h - 16)
        win = bytes(img[lo - IB: min(TEXT_HI, h + 17) - IB])
        for insn in md.disasm(win, lo):
            if insn.address + insn.size <= h:
                continue
            if insn.address > h:
                break
            for op in (ops(insn) or []):
                if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
                        and (op.mem.disp & 0xFFFFFFFF) == va:
                    ok.append(insn.address)
                    break
            break
    return ok


def ctor_vtable(base):
    """the vftable stored into [base] by the static ctor, and its class name.

    Byte-exact: the MSVC static ctor always emits
        C7 05 <base:4> <vftable:4>      mov dword ptr [base], imm32
    so match that pattern directly instead of trying to re-decode a window that
    may start mid-instruction.  Both the base (`VectorClass<T>`) and the derived
    (`DynamicVectorClass<T>`) vtable get stored -- ctor then dtor -- so prefer
    the DynamicVectorClass one, which is what a fully constructed object holds.
    """
    pat = b"\xC7\x05" + struct.pack("<I", base)
    cands = []
    i = text.find(pat)
    while i >= 0:
        at = TEXT_LO + i
        vt = struct.unpack_from("<I", text, i + 6)[0]
        col = u32(vt - 4) if has_bytes(vt - 4) else None
        ptd = u32(col + 0x0C) if col else None
        nm = TD.get(ptd)
        if nm:
            cands.append((at, vt, col, ptd, nm))
        i = text.find(pat, i + 1)
    if not cands:
        return None
    dyn = [c for c in cands if "DynamicVectorClass" in c[4]]
    pick = (dyn or cands)[0]
    return pick[1], pick[2], pick[3], pick[4]


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


def short(mangled):
    """.?AV?$DynamicVectorClass@PAVBuildingClass@@@@ -> DynamicVectorClass<BuildingClass*>"""
    if not mangled:
        return ""
    s = mangled
    for p in (".?AV", ".?AU"):
        if s.startswith(p):
            s = s[len(p):]
            break
    s = s.rstrip("@")
    if not s.startswith("?$"):
        return s
    body = s[2:]                      # DynamicVectorClass@PAVBuildingClass
    if "@" not in body:
        return body
    name, arg = body.split("@", 1)
    arg = arg.rstrip("@")
    is_const = False
    depth = 0
    if arg.startswith("PB"):
        is_const, arg, depth = True, arg[2:], 1
    elif arg.startswith("PA"):
        arg, depth = arg[2:], 1
    if depth and arg[:1] in ("V", "U"):
        arg = arg[1:]
    return "%s<%s%s%s>" % (name, "const " if is_const else "", arg,
                           "*" if depth else "")


rows = []
print("%-26s %-10s %-10s %-10s %-12s %-8s %s"
      % ("element (from binary RTTI)", "base", "Items", "Count", "vftable", "itemsRef", "countRef"))
print("-" * 108)
for typ, base in YRPP:
    got = ctor_vtable(base)
    if got:
        vt, col, ptd, nm = got
        el = short(nm)
    else:
        vt = col = ptd = None
        el = "(no ctor vtable found)"
    ni, nc = len(refs(base + 4)), len(refs(base + 0x10))
    agree = "yes" if (got and typ.rstrip("*") in (el or "")) else ("?" if not got else "NO")
    rows.append((el, base, base + 4, base + 0x10, vt, col, ptd, ni, nc, typ, agree))
    print("%-26s 0x%08X 0x%08X 0x%08X %-12s %-8d %d  %s"
          % (el[:26], base, base + 4, base + 0x10,
             ("0x%08X" % vt) if vt else "-", ni, nc, agree))

named = sum(1 for r in rows if r[4])
agree = sum(1 for r in rows if r[10] == "yes")
print("\n  named by the binary's own RTTI : %d / %d" % (named, len(rows)))
print("  YRpp element type agrees       : %d / %d" % (agree, len(rows)))

out = os.path.join(HERE, "instance_arrays.tsv")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("element\tbase\titems\tcount\tvftable\tcol\ttd\titems_refs\tcount_refs\tyrpp_type\tyrpp_agrees\n")
    for el, base, it, cn, vt, col, ptd, ni, nc, typ, ag in rows:
        f.write("%s\t0x%08X\t0x%08X\t0x%08X\t%s\t%s\t%s\t%d\t%d\t%s\t%s\n"
                % (el, base, it, cn,
                   ("0x%08X" % vt) if vt else "", ("0x%08X" % col) if col else "",
                   ("0x%08X" % ptd) if ptd else "", ni, nc, typ, ag))
print("  wrote %s" % out)
