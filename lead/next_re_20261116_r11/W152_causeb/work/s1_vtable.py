"""S1: dump the BuildingClass main vtable (0x7E3EBC) slot by slot, plus the
chain functions' own entries.  Pure file reads -- no Ghidra, no live process.

Run:  python s1_vtable.py > ..\\EVIDENCE\\s1_vtable.log 2>&1
"""
import sys
import w152_core as C

VT_BUILDING = 0x007E3EBC   # BuildingClass 主虚表, §650-1 (COL offset==0)

print("ImageBase = %08X" % C.IB)
print("BuildingClass main vtable = %08X" % VT_BUILDING)
print("COL at vt-4 = %08X" % C.u32(VT_BUILDING - 4))

# --- how far can the slot array run? stop at first dword that is neither a
# --- plausible code address nor a known COL cluster constant (§3.1 v2 rule).
KNOWN_CONST = {0x404E0000, 0xA2529D39, 0x3F91DF46}
slots = []
i = 0
while i < 400:
    v = C.u32(VT_BUILDING + 4 * i)
    if v in KNOWN_CONST or v == 0:
        print("stop at slot %d (0x%X): value %08X" % (i, 4 * i, v))
        break
    nm, vs, _, _ = C.sec_of(v)
    if nm != '.text':
        print("stop at slot %d (0x%X): value %08X section=%s" % (i, 4 * i, v, nm))
        break
    slots.append(v)
    i += 1

print("slot count read = %d" % len(slots))
print("")
print("SLOTS (index / offset / target / atlas entry / size)")
for idx, v in enumerate(slots):
    e = C.owning_fn(v)
    print("  %3d  0x%03X  %08X  entry=%s  %s" % (
        idx, 4 * idx, v, "yes" if e == v else ("in " + C.fn_label(e) if e else "NO"),
        ("size=%s" % C.fn_size(v)) if v in C.FUNC else ""))

print("")
print("=== named slots of interest ===")
for idx in (0, 1, 2, 73, 179, 337, 66, 34, 30, 110):
    if idx < len(slots):
        v = slots[idx]
        print("  slot %3d (0x%03X) -> %08X  size=%s" % (
            idx, 4 * idx, v, C.fn_size(v) if v in C.FUNC else "NOT-A-FUNC-ENTRY"))

# --- the two chain functions and the Add/Remove primitives: confirm entries
print("")
print("=== chain-family entries (atlas) ===")
for a in (0x005683C0, 0x005687F0, 0x0047E8A0, 0x0047EA90, 0x0047D2B0, 0x0048DEE0,
          0x0043F180, 0x0043FB20, 0x004D3780, 0x0071BFB0):
    print("  %08X  in_atlas=%s size=%s owner=%s" % (
        a, a in C.FUNC, C.fn_size(a), C.fn_label(C.owning_fn(a))))
