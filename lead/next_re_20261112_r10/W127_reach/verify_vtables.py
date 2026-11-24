#!/usr/bin/env python3
"""W127i: verify EVERY vtable attribution the report makes, from raw bytes.

MSVC RTTI layout confirmed by reading bytes (not assumed):
  [vt-4] -> COL ; COL+0x0C -> TypeDescriptor ; TD+0x08 -> inline char[] name
(An earlier note in the ledger assumed TD+0x08 was a *pointer*; it is inline.)

Also verifies the dynamic slot value equals the function we attribute.
"""
import struct
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()


def u32(va):
    return struct.unpack("<I", img[va - ib:va - ib + 4])[0]


def rtti(vt):
    col = u32(vt - 4)
    ptd = u32(col + 0x0C)
    raw = img[ptd + 0x08 - ib:ptd + 0x08 - ib + 80]
    name = raw.split(b"\x00")[0].decode("latin-1", "replace")
    return col, ptd, name


# (vtable_start, slot, expected function, what it is)
CASES = [
    (0x007F0344, 34, 0x00654320, "site1  (RadarClass?)"),
    (0x007EDFB4, 34, 0x006ABD30, "site2/3 (TabClass)"),
    (0x007F1094, 34, 0x006ABD30, "site2/3 (ScrollClass)"),
    (0x007F3058, 34, 0x006ABD30, "site2/3 (SidebarClass)"),
    (0x007EDFB4, 54, 0x006D04F0, "site4-6 (TabClass)"),
    (0x007F1094, 54, 0x006D04F0, "site4-6 (ScrollClass)"),
    (0x007EDFB4, 10, 0x006D0680, "site7-9 (TabClass)"),
    (0x007F1094, 10, 0x006922E0, "site7-9 (ScrollClass -> wrapper)"),
    (0x007EA8A0, 23, 0x004F8440, "crash-entry caller (HouseClass)"),
]

print("%-34s %-10s %-9s %-24s %s" % ("vtable", "slot", "value", "class (RTTI)", "match"))
print("-" * 110)
allok = True
for vt, slot, expect, label in CASES:
    addr = vt + 4 * slot
    val = u32(addr)
    col, ptd, name = rtti(vt)
    ok = (val == expect)
    allok &= ok
    print("%-34s %-10d 0x%08X %-24s %s   %s"
          % ("0x%08X @0x%08X" % (vt, addr), slot, val, name,
             "OK" if ok else "MISMATCH(expected 0x%08X)" % expect, label))

print("\nall attributions consistent:", allok)

# the 4th container that holds 0x6ABD30 (class=None in the earlier map)
print("\n=== unnamed container at 0x7E1958 ===")
col, ptd, name = rtti(0x007E1958)
print("  [0x7E1954]=COL 0x%08X  TD=0x%08X  name=%r" % (col, ptd, name))
for slot in range(0, 40):
    v = u32(0x007E1958 + 4 * slot)
    if v == 0x006ABD30:
        print("  holds 0x6ABD30 at slot %d (0x%08X)" % (slot, 0x007E1958 + 4 * slot))
