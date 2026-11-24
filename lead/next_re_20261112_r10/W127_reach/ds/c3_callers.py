"""C3 part 4 (final for C3): 
 (a) The TD name pointer base differs from what the task's recipe implies.
     The recipe says TD+0x08 -> name. Read literally, u32(0x816C70+0x08) is
     0x56413F2E (garbage). The real pointer is at TD+0x0C = 0x816C78.
     So this binary's TypeDescriptor has an extra dword. VERIFY.
 (b) Callers of 0x006D0680: is 0x6922E0 the ONLY direct caller?
 (c) For every vtable slot in the whole .rdata, does any slot hold the
     trampoline/reference to 0x6D0680 other than 0x6922E0?
 (d) Is 0x6922E0 reached via virtual dispatch? Show the vtable slot and the
     indirection that would use it.
"""
from base import BUF, IB, u32, s32, cstr, in_raw, blob, SECTIONS, TEXT
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)

print("=== (a) TypeDescriptor raw layout ===")
td = 0x00816C70
print("  raw 0x%08X..: %s" % (td, blob(td, 0x14).hex()))
for i in range(0, 0x14, 4):
    v = u32(td + i)
    interp = ""
    if in_raw(v, 4) and 0x007E1000 <= v < 0x00811074:
        interp = "(.rdata ptr)"
    if in_raw(v, 2) and 0x00812000 <= v < 0x00B79BE4:
        s = cstr(v, 32)
        if s:
            interp = "(-> %r)" % s
    print("    TD+0x%02X = %08X %s" % (i, v, interp))
print("  CONCLUSION: name pointer is at TD+0x0C = 0x816C78 -> %r"
      % cstr(0x00816C78, 40))
print("  The recipe 'TD+0x08 is the name' holds only if TD is read as 0x816C74;")
print("  i.e. this build's TD has vftable at +0x00, spare at +0x04, and")
print("  some field at +0x08 (0x00000000), name at +0x0C.")

print()
print("=== (b) direct callers of 0x006D0680 across .text ===")
tgt = 0x006D0680
callers = []
for va in range(TEXT["va"], TEXT["va"] + TEXT["vsize"] - 5):
    i = va - IB
    if BUF[i] in (0xE8, 0xE9):
        t = va + 5 + s32(va + 1)
        if t == tgt:
            callers.append((va, "call" if BUF[i] == 0xE8 else "jmp"))
print("  direct call/jmp sites (%d): %s" % (len(callers),
      [("%s@%08X" % (k, a)) for a, k in callers]))
# also dword == tgt anywhere (function pointer class)
ptrs = []
for s in SECTIONS:
    for va in range(s["va"], s["va"] + s["rawsize"] - 3):
        if u32(va) == tgt:
            ptrs.append((s["name"], va))
print("  dword == 0x%08X in file bytes: %s" % (tgt, [("%s:%08X" % x) for x in ptrs]))

print()
print("=== (c) who calls 0x006922E0 (the trampoline)? ===")
tgt2 = 0x006922E0
c2 = []
for va in range(TEXT["va"], TEXT["va"] + TEXT["vsize"] - 5):
    i = va - IB
    if BUF[i] in (0xE8, 0xE9):
        if va + 5 + s32(va + 1) == tgt2:
            c2.append(va)
c2d = []
for s in SECTIONS:
    for va in range(s["va"], s["va"] + s["rawsize"] - 3):
        if u32(va) == tgt2:
            c2d.append((s["name"], va))
print("  direct call/jmp to 0x6922E0: %s" % ["%08X" % a for a in c2])
print("  dword slots holding 0x6922E0: %s" % [("%s:%08X" % x) for x in c2d])

print()
print("=== (d) full vtable inventory: which tables hold 0x6922E0 and at what index? ===")
# build vtable list: a dword pointing into .rdata followed by code ptrs
rd_lo, rd_hi = 0x007E1000, 0x00811074
def is_code(v):
    return TEXT["va"] <= v < TEXT["va"] + TEXT["vsize"]

vt_starts = []
for v in range(rd_lo + 4, rd_hi - 4, 4):
    col = u32(v - 4)
    if rd_lo <= col < rd_hi and in_raw(col, 0x18) and is_code(u32(v)):
        prev = u32(v - 8) if v - 8 >= rd_lo else 0
        if not is_code(prev):
            vt_starts.append(v)
print("  candidate vtable starts: %d" % len(vt_starts))

for v in vt_starts:
    entries = []
    a = v
    while a + 4 <= rd_hi and is_code(u32(a)):
        entries.append(u32(a))
        a += 4
    if tgt2 in entries:
        idx = entries.index(tgt2)
        col = u32(v - 4)
        tdp = u32(col + 0xC)
        nm = cstr(u32(tdp + 0xC), 40) if in_raw(tdp, 0x10) else None
        print("  vt=%08X  n=%d  slot=%d  COL=%08X  class=%r" %
              (v, len(entries), idx, col, nm))

print()
print("=== (e) the 3 unchecked call sites inside 0x6D0680 and the entry guard ===")
lo, hi = 0x006D0680, 0x006D0A20
for ins in md.disasm(bytes(BUF[lo - IB: hi - IB]), lo):
    if ins.address in (0x006D0896, 0x006D08A8, 0x006D0935):
        print("  >>> %08X  %-9s %s" % (ins.address, ins.mnemonic, ins.op_str))
    elif ins.mnemonic == "ret":
        print("      %08X  ret  <<< function end?" % ins.address)
