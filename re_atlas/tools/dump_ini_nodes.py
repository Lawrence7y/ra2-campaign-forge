"""R-016: recover the INI container layout (INIClass / CCINIClass / INISection /
INIEntry) and the section lookup mechanism.

Why this exists: R-015 hand-read the constructors and got two things wrong
(see kb/30_ini_subsystem.md section 8). This tool makes every one of those
calls re-derivable from bytes instead of from prose.

The two traps this tool is written around, both of which R-015 fell into:

1. `.rdata` tables are packed head-to-tail, so "the table right after a COL"
   is usually a DIFFERENT class. Every table attributed here is resolved via
   its own `[vt-4]` COL, and COL detection is validated against a known-good
   baseline (AbstractClass) before any result is trusted.

2. A `mov dword ptr [esi], <vtable>` inside a *destructor* restores the vtable
   as part of the unwind; it does NOT mean the object is being constructed or
   that it inherits the class owning that vtable. R-015 read 0x4F2B60 that way
   and concluded `INIClass : VectorClass<GraphicMenuItem*>`. 0x4F2B60 is that
   vector class's destructor, reached from a neighbouring table.

Run: python re_atlas/tools/dump_ini_nodes.py
"""

import struct

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074
DATA_LO, DATA_HI = 0x812000, 0xB79BE4

with open(EXE, "rb") as fh:
    BLOB = fh.read()


def read_va(va, n):
    # .text/.rdata/.data are all VA - 0x400000. BSS has no file backing.
    fo = va - IMAGE_BASE
    if fo < 0 or fo >= len(BLOB):
        return b""
    return BLOB[fo:fo + n]


def u32(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def cstr(va, n=160):
    b = read_va(va, n)
    if not b:
        return ""
    z = b.find(b"\x00")
    return b[:z].decode("ascii", "replace") if z >= 0 else b.decode("ascii", "replace")


def tdesc_name(td):
    """TypeDescriptor: +0x00 vftable, +0x04 spare, +0x08 name."""
    return cstr(td + 8)


def col_of(vtable):
    """vtable[-1] -> CompleteObjectLocator, then COL+0x0C -> TypeDescriptor.

    CompleteObjectLocator (x86, single inheritance):
        +0x00 signature, +0x04 offset, +0x08 cdOffset,
        +0x0C pTypeDescriptor, +0x10 pClassDescriptor, +0x14 self
    """
    col = u32(vtable - 4)
    if col is None:
        return None
    sig, off, cd = (u32(col), u32(col + 4), u32(col + 8))
    ptd = u32(col + 0xC)
    return {"col": col, "sig": sig, "off": off, "cd": cd, "ptd": ptd,
            "name": tdesc_name(ptd) if ptd else None}


def find_cols(td_names):
    """Locate CompleteObjectLocators that point at the given TypeDescriptors.

    A real COL has signature 0, cdOffset 0, and a pTypeDescriptor that lands
    in the TypeDescriptor region. Scanning for "a dword equal to pTD" alone is
    NOT enough: the TDs themselves reference each other, so that test yields
    false COLs pointing at TypeDescriptor memory (R-016 first attempt).
    """
    out = []
    for lo, hi in ((RDATA_LO, RDATA_HI), (DATA_LO, DATA_HI)):
        for va in range(lo, hi - 0x18, 4):
            sig, off, cd = u32(va), u32(va + 4), u32(va + 8)
            # BSS has no file bytes: u32 returns None and the scan skips.
            if sig is None or sig != 0 or cd != 0:
                continue
            ptd = u32(va + 0xC)
            if ptd in td_names:
                out.append((va, td_names[ptd], off))
    return out


def vtables_pointing_at(col_vas):
    """A vtable starts right after the dword that references its COL."""
    out = {}
    for lo, hi in ((RDATA_LO, RDATA_HI), (DATA_LO, DATA_HI)):
        for va in range(lo, hi - 4, 4):
            v = u32(va)
            if v is None:
                continue
            if v in col_vas:
                out[col_vas[v]] = va + 4
    return out


def disas(va, n=400, max_bytes=0x300):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    out = []
    for insn in md.disasm(read_va(va, max_bytes), va):
        out.append((insn.address, insn.bytes.hex(" "), insn.mnemonic, insn.op_str))
        if insn.mnemonic.startswith("ret"):
            break
        if len(out) >= n:
            break
    return out


# --- CRC32 table -----------------------------------------------------------
# 0x4A1FB0 is a CRC32 update step: `not eax` ... `not eax` around the loop,
# indexed through a 256-entry table. The table identity is the whole claim, so
# compare all 256 entries rather than sampling.
def crc32_table_matches(va):
    std = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        std.append(c)
    bad = [i for i in range(256) if u32(va + 4 * i) != std[i]]
    return (not bad), bad[:8]


def main():
    print("=== positive control: COL decode on a class whose name is already "
          "established (AbstractClass, vtable 0x007E1F50) ===")
    ctl = col_of(0x007E1F50)
    print(f"  [0x7E1F4C] = COL 0x{ctl['col']:08X}  sig={ctl['sig']} off={ctl['off']} "
          f"cd={ctl['cd']}  name={ctl['name']!r}")
    if ctl["name"] != ".?AVAbstractClass@@":
        print("  !! control FAILED -- COL decode is wrong, every result below is void")
        return 1
    print("  control OK")

    print("\n=== CRC32 table (0x0081F7B4) ===")
    ok, bad = crc32_table_matches(0x81F7B4)
    print(f"  all 256 entries == standard reflected CRC32 polynomial table: {ok}"
          + ("" if ok else f"  mismatches at {bad}"))

    print("\n=== INI container classes ===")
    known = {
        0x00825AF0: "INIEntry",
        0x00825B40: "INISection",
        0x00825AC0: "Node<INIEntry*>",
        0x00825B10: "Node<INISection*>",
        0x00825A90: "List<INIEntry*>",
        0x00817480: "List<INISection*>",
        0x008174B0: "INIClass",
        0x008174C8: "CCINIClass",
    }
    for td, label in known.items():
        print(f"  TD 0x{td:08X}  {tdesc_name(td):40s} ({label})")

    cols = find_cols(known)
    print(f"\n=== CompleteObjectLocators ({len(cols)}) ===")
    for va, label, off in cols:
        print(f"  COL 0x{va:08X}  {label:20s} offset={off}  "
              f"TD name={tdesc_name(u32(va + 0xC))!r}")

    col_map = {va: label for va, label, off in cols}
    vts = vtables_pointing_at(col_map)
    print("\n=== vtables (resolved via their own COL, not by adjacency) ===")
    for label, vt in sorted(vts.items(), key=lambda kv: kv[1]):
        slots = []
        for i in range(0, 8):
            v = u32(vt + 4 * i)
            if v is None:
                break
            slots.append(f"0x{v:08X}")
            # a COL reference or a non-.text value means the table ended
            if not (TEXT_LO <= v < TEXT_HI) and i > 0:
                slots.pop()
                break
        print(f"  {label:20s} vtable 0x{vt:08X}  slots={slots}")

    print("\n=== INISection ctor: allocation size and field writes "
          "(0x00525DEA region) ===")
    for addr, raw, mn, ops in disas(0x525DD0, max_bytes=0x90):
        if mn in ("push", "call", "mov", "lea") and (
                "0x44" in ops or "0x7eb7" in ops or "ebx +" in ops or mn == "call"):
            print(f"  0x{addr:08X}  {raw:<21} {mn} {ops}")

    print("\n=== CCINIClass ctor field writes (0x00535AA0) ===")
    for addr, raw, mn, ops in disas(0x535AA0, max_bytes=0xB0):
        print(f"  0x{addr:08X}  {raw:<21} {mn} {ops}")

    print("\n=== GetSection (0x00526810): lookup is hash-only ===")
    for addr, raw, mn, ops in disas(0x526810, max_bytes=0x160):
        if mn in ("mov", "cmp", "call", "jmp") and any(
                k in ops for k in ("esi + 0x28", "esi + 0x2c", "esi + 0x30",
                                   "esi + 0x34", "esi + 0x38", "0x4a1de0",
                                   "0x52b720", "0x52b750")):
            print(f"  0x{addr:08X}  {raw:<21} {mn} {ops}")

    print("\n  comparator 0x0052B720 compares ONLY the first dword (the hash):")
    for addr, raw, mn, ops in disas(0x52B720, max_bytes=0x30, n=16):
        print(f"  0x{addr:08X}  {raw:<21} {mn} {ops}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
