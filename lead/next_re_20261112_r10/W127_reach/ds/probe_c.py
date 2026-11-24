from base import BUF, IB, u32, s32, cstr, in_raw, blob, TEXT
rd_lo, rd_hi = 0x007E1000, 0x00811074
def is_code(v): return TEXT["va"] <= v < TEXT["va"] + TEXT["vsize"]

print("=== vtable 0x7EDFB4 (holds 0x6D0680 directly at slot 10) ===")
vt = 0x007EDFB4
col = u32(vt - 4)
print("  col ptr (vt-4=0x%08X) = %08X" % (vt-4, col))
print("  col raw 0x%08X..: %s" % (col, blob(col, 0x18).hex() if in_raw(col,0x18) else "n/a"))
if in_raw(col, 0x18):
    for i in range(0, 0x18, 4):
        print("     COL+0x%02X = %08X" % (i, u32(col+i)))
print()
print("  slots:")
for k in range(14):
    v = u32(vt + 4*k)
    print("     slot %-2d %08X %s" % (k, v, "<<< 0x6D0680" if v == 0x006D0680 else ""))
print()
print("=== TD name: resolve properly ===")
def tdname(tdp):
    if not in_raw(tdp, 0x10): return None
    for off in (0x0C, 0x10, 0x08):
        p = u32(tdp + off)
        if in_raw(p, 4):
            s = cstr(p, 48)
            if s.startswith(".?A") or s.startswith(".?U") or s.startswith("?A"):
                return (off, p, s)
    return None
for label, tdp in (("0x7F1094's TD", 0x00816C70), ("0x7EDFB4's TD", u32(col+0xC) if in_raw(col,0x18) else 0)):
    if tdp:
        print("  %s @%08X -> %s" % (label, tdp, tdname(tdp)))

print()
print("=== and the 0x7EDFB4 family: is it a base of the 0x7F1094 one? compare slot lists ===")
A = [u32(0x007F1094 + 4*k) for k in range(55)]
Bv = [u32(0x007EDFB4 + 4*k) for k in range(45)]
print("  0x7F1094[0:12] =", ["%08X" % x for x in A[:12]])
print("  0x7EDFB4[0:12] =", ["%08X" % x for x in Bv[:12]])
print("  common suffix length:", end=" ")
n = 0
while n < min(len(A), len(Bv)) and A[-1-n] == Bv[-1-n]:
    n += 1
print(n)
