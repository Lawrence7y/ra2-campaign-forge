from base import BUF, IB, u32, s32, cstr, in_raw, blob, TEXT, RDATA
rd_lo, rd_hi = 0x007E1000, 0x00811074
def is_code(v): return TEXT["va"] <= v < TEXT["va"] + TEXT["vsize"]

# Proper vtable detection: COL ptr is a dword P where in_rdata(P) and
# u32(P+0x10) is a dword whose value is itself in .rdata (pSelf pattern) or
# u32(P+0x0C) is a TD in .data. Use: preceded by dword that is NOT a code ptr
# AND following dwords are code ptrs, AND max run.
runs = []
i = rd_lo
while i < rd_hi - 4:
    if is_code(u32(i)):
        j = i
        while j < rd_hi - 4 and is_code(u32(j)):
            j += 4
        n = (j - i)//4
        if n >= 3:
            runs.append((i, j, n))
        i = j
    else:
        i += 4

vt = []
for s, e, n in runs:
    if s - 4 >= rd_lo:
        col = u32(s - 4)
        if rd_lo <= col < rd_hi and in_raw(col, 0x1C):
            vt.append((s, e, n, col))

print("=== vtables with a COL pointer at vt-4 and >=3 slots: %d ===" % len(vt))
print("=== those whose slot list contains 0x006922E0 ===")
tgt2 = 0x006922E0
for s, e, n, col in vt:
    ents = [u32(s + 4*k) for k in range(n)]
    if tgt2 in ents:
        idx = ents.index(tgt2)
        tdp = u32(col + 0xC)
        nm14 = cstr(u32(tdp + 0x10), 40) if in_raw(tdp + 0x10, 4) else None
        nm1c = cstr(u32(tdp + 0xC), 40) if in_raw(tdp + 0xC, 4) else None
        print("  vt=%08X n=%d slot=%d col=%08X TD=%08X name(+0x0C)=%r" %
              (s, n, idx, col, tdp, nm1c))

print()
print("=== the specific one at 0x7F1094: recompute from the proper run ===")
for s, e, n, col in vt:
    if s == 0x007F1094:
        print("  vt=007F1094  n=%d  col=%08X" % (n, col))
        ents = [u32(s + 4*k) for k in range(n)]
        for k in range(min(n, 12)):
            print("     slot %-2d %08X  %s" % (k, ents[k], "<<< 0x6922E0" if ents[k]==tgt2 else ""))
        if tgt2 in ents:
            print("  -> 0x6922E0 is slot %d" % ents.index(tgt2))

print()
print("=== ALL vtables whose slot table contains 0x6D0680 directly ===")
for s, e, n, col in vt:
    ents = [u32(s + 4*k) for k in range(n)]
    if 0x006D0680 in ents:
        print("  vt=%08X slot=%d" % (s, ents.index(0x006D0680)))

print()
print("=== does 0x7EDFDC form a vtable-shaped run with a COL at 0x7EDFD8? ===")
cand = 0x007EDFD8
print("  u32(%08X) = %08X (in .rdata: %s)" % (cand, u32(cand), rd_lo <= u32(cand) < rd_hi))
for s, e, n, col in vt:
    if s == 0x007EDFDC:
        print("  YES: vtable at 0x7EDFDC with col=%08X n=%d, 0x6D0680 at slot %d" %
              (col, n, [u32(s+4*k) for k in range(n)].index(0x006D0680)))
        break
else:
    print("  0x7EDFDC is not registered as a vtable start in my detector")
    # show what COL would be
    col = u32(0x007EDFDC - 4)
    print("  col candidate = %08X  raw=%s" % (col, blob(col, 0x1C).hex() if in_raw(col,0x1C) else "n/a"))
    # how long is the code ptr run beginning at 0x7EDFDC?
    j = 0x007EDFDC
    while is_code(u32(j)) and j < rd_hi - 4:
        j += 4
    print("  code-ptr run from 0x7EDFDC ends at %08X (n=%d)" % (j, (j-0x007EDFDC)//4))
    print("  entries: %s" % ["%08X" % u32(0x007EDFDC + 4*k) for k in range((j-0x007EDFDC)//4)])
