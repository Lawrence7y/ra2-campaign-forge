"""C3 part 2: (a) full vtable extent from the table start, (b) is 0x7F1094
even a vtable start, (c) where is .?AVScrollClass@@ in the WHOLE image,
(d) what is the COL layout actually used by this binary?

Do not assume the MSVC VC6 vs VC7+ offset layout -- read the bytes.
"""
from base import BUF, IB, u32, s32, cstr, in_raw, blob, SECTIONS, TEXT

print("=== A. scan for '.?AVScrollClass@@' anywhere in file bytes ===")
needle = b".?AVScrollClass@@"
for s in SECTIONS:
    lo, hi = s["va"], s["va"] + s["rawsize"]
    for va in range(lo, hi - len(needle)):
        if bytes(BUF[va - IB: va - IB + len(needle)]) == needle:
            print("  %-8s @%08X  ctx=%r" % (s["name"], va, cstr(va, 64)))

print()
print("=== B. all class-name strings containing 'Scroll' in file bytes ===")
s_needle = b"Scroll"
lo, hi = 0x007E1000, 0x00811074
seen = set()
for va in range(lo, hi - 8):
    if bytes(BUF[va - IB: va - IB + 6]) == s_needle:
        if in_raw(va, 4):
            print("  @%08X  %r" % (va, cstr(va, 48)))

print()
print("=== C. walk backwards from 0x7F1094 to find the real vtable start ===")
print("   looking for the run of code pointers that begins this table")
def is_code_ptr(v):
    return TEXT["va"] <= v < TEXT["va"] + TEXT["vsize"]
va = 0x007F1094
# walk backwards while dwords are code pointers
back = va
while back - 4 >= 0x007E1000 and is_code_ptr(u32(back - 4)):
    back -= 4
print("   contiguous code-pointer run starts at %08X (i.e. %08X is mid-table if != 0x7F1094)"
      % (back, va))
fwd = back
while fwd + 4 < 0x00811074 and is_code_ptr(u32(fwd)):
    fwd += 4
print("   and ends at %08X  (length %d entries)" % (fwd, (fwd - back) // 4))
print("   table dump %08X..%08X:" % (back, fwd))
i = 0
for a in range(back, fwd, 4):
    mark = "  <<< 0x7F1094" if a == 0x007F1094 else ""
    mark = "  <<< slot-10 claim addr 0x7F10BC" if a == 0x007F10BC else mark
    print("     entry %-3d %08X  %08X%s" % (i, a, u32(a), mark))
    i += 1
print("   dword right before table start: %08X %08X (COL ptr candidate)"
      % (back - 4, u32(back - 4)))

print()
print("=== D. empirical COL layout: test many COLs for which offsets look sane ===")
# For each vtable start (preceded by a dword pointing into .rdata), see whether
# COL+0x0C or COL+0x10 points to a TD whose +8 points at a '?AV' string.
def td_ok(td):
    if not in_raw(td, 0x10):
        return None
    np = u32(td + 8)
    if not in_raw(np, 4):
        return None
    nm = cstr(np, 64)
    if nm.startswith(".?A") or nm.startswith(".?U"):
        return nm
    return None

lo_r, hi_r = 0x007E1000, 0x00811074
results = []
for v in range(lo_r + 4, hi_r - 4):
    col = u32(v - 4)
    if not (lo_r <= col < hi_r) or not in_raw(col, 0x18):
        continue
    if not is_code_ptr(u32(v)):
        continue
    nm12 = td_ok(u32(col + 0xC))
    nm14 = td_ok(u32(col + 0x10))
    if nm12 or nm14:
        results.append((v, col, nm12, nm14))

print("  vtables found with a resolvable RTTI name: %d" % len(results))
from collections import Counter
c12 = sum(1 for r in results if r[2])
c14 = sum(1 for r in results if r[3])
print("  COL+0x0C resolves to a name: %d" % c12)
print("  COL+0x10 resolves to a name: %d" % c14)
print()
print("  samples:")
for v, col, n12, n14 in results[:12]:
    print("    vt=%08X col=%08X  COL+0x0C->%-28s COL+0x10->%-28s" %
          (v, col, n12, n14))

print()
print("=== E. is 0x7F1094's own COL (0x809060) resolvable under the winning layout? ===")
col = u32(0x007F1094 - 4)
print("  col=%08X raw=%s" % (col, blob(col, 0x18).hex()))
print("  COL+0x0C = %08X -> name %r" % (u32(col + 0xC), td_ok(u32(col + 0xC))))
print("  COL+0x10 = %08X -> name %r" % (u32(col + 0x10), td_ok(u32(col + 0x10))))
