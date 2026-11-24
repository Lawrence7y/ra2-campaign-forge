"""C3 part 1: read the RTTI chain for the vtable whose slot 10 is claimed to be
0x006922E0. Per the task, MSVC RTTI:
   [vt-4]            -> Complete Object Locator (COL)
   COL + 0x0C        -> signature
   COL + 0x10        -> offset
   COL + 0x14        -> pTypeDescriptor
   TD  + 0x00        -> vftable pointer of type_info
   TD  + 0x08        -> ".?AV...@@" name

VERIFY each of those by reading bytes; if the layout differs I say so.
"""
from base import BUF, IB, u32, s32, u16, cstr, in_raw, blob

def dump(va, n, label=""):
    print("  %s @%08X (%d bytes, raw-backed=%s): %s" %
          (label, va, n, in_raw(va, n), blob(va, n).hex()))

print("=== 1. the vtable window 0x7F1094..0x7F10C0 (claimed slot 10 @0x7F10BC) ===")
vt = 0x007F1094
for i in range(0, 24, 4):
    a = vt + i
    print("  vt+%2d  %08X  dword=%08X  (slot %d)" % (i, a, u32(a), i // 4))

print()
print("=== 2. slot 10 arithmetic ===")
print("  (0x7F10BC - 0x7F1094) / 4 =", (0x7F10BC - 0x7F1094) // 4)
print("  note: MSVC RTTI places the COL pointer at vt-4 = %08X" % (vt - 4))
print("  so if slot indices are counted from vt itself, slot 10 == 0x%08X" %
      (vt + 40))
print("  dword at 0x7F10BC =", "0x%08X" % u32(0x007F10BC))

print()
print("=== 3. [vt-4] -> COL ===")
for cand in (vt - 4, vt):
    p = u32(cand)
    print("  u32(%08X) = %08X   (in .rdata? %s, raw=%s)" %
          (cand, p, "yes" if 0x007E1000 <= p < 0x00811074 else "no", in_raw(p, 4)))

# Which of vt-4 / vt points at something that looks like a COL?
def looks_like_col(p):
    if not in_raw(p, 0x18):
        return False
    sig = u32(p)
    off = s32(p + 0x8)
    cod = u32(p + 0xC)
    td  = u32(p + 0x10)
    ptd = u32(p + 0x14)
    ok_td = in_raw(td, 0x10) or in_raw(ptd, 0x10)
    return (sig in (0, 1)) and 0x007E1000 <= cod < 0x00811074 and ok_td

for cand in (vt - 4, vt):
    p = u32(cand)
    print("  cand=%08X -> %08X  looks_like_COL=%s" % (cand, p, looks_like_col(p)))

print()
print("=== 4. locate the COL for slot-10 vtable: try both interpretations ===")
for base_label, base in (("vt", vt), ("vt-4", vt - 4)):
    col = u32(base - 4) if base_label == "vt" else u32(base)
    print("  interpretation %-5s: COL ptr = %08X" % (base_label, col))
    if in_raw(col, 0x1C):
        dump(col, 0x1C, "COL raw")
        sig = u32(col)
        off = s32(col + 0x8)
        cod = u32(col + 0xC)
        td  = u32(col + 0x10)
        ptd = u32(col + 0x14)
        print("    +0x00 signature      = %08X" % sig)
        print("    +0x04 offset(mdisp)  = %08X" % u32(col + 4))
        print("    +0x08 cdOffset       = %d" % off)
        print("    +0x0C pTypeDescriptor= %08X" % cod)
        print("    +0x10 ?alt           = %08X" % td)
        print("    +0x14 ?alt2          = %08X" % ptd)
        for lbl, t in (("+0x0C", cod), ("+0x10", td), ("+0x14", ptd)):
            if in_raw(t, 0x10):
                print("      TD candidate from COL%s @%08X:" % (lbl, t))
                print("        +0x00 vftable ptr = %08X" % u32(t))
                print("        +0x04 spare       = %08X" % u32(t + 4))
                print("        +0x08 name ptr    = %08X" % u32(t + 8))
                np = u32(t + 8)
                if in_raw(np, 8):
                    print("        name string       = %r" % cstr(np))
    print()

print("=== 5. global sanity: find the COL that names .?AVScrollClass@@ ===")
# search .rdata for the name string then walk back to a TD whose +8 points at it
lo, hi = 0x007E1000, 0x00811074
target_name = b".?AVScrollClass@@"
name_vas = []
for va in range(lo, hi - len(target_name)):
    if bytes(BUF[va - IB: va - IB + len(target_name)]) == target_name:
        name_vas.append(va)
print("  occurrences of .?AVScrollClass@@ in .rdata:", ["%08X" % x for x in name_vas])
for nv in name_vas:
    # TD is 8..0x10 bytes before the name start at +8
    for td in range(nv - 0x18, nv):
        if in_raw(td, 0x10) and u32(td + 8) == nv:
            print("    TD @%08X -> name @%08X" % (td, nv))
            # find COLs pointing at this TD
            cols = []
            for c in range(lo, hi - 0x1C):
                if u32(c + 0x10) == td or u32(c + 0xC) == td or u32(c + 0x14) == td:
                    cols.append(c)
            print("      COLs referencing TD: %s" % ["%08X" % c for c in cols])
            # find vtables whose [vt-4] == one of those COLs
            for c in cols:
                vts = []
                for v in range(lo, hi - 4):
                    if u32(v) == c:
                        vts.append(v + 4)   # vt = position after COL ptr
                print("      vtables (addrs whose dword==COL): %s" %
                      ["%08X" % x for x in vts])
