"""C2 part 2: establish the ACTUAL function boundaries in 0x6D1400..0x6D17FF
by decoding, instead of trusting the claimed extents.

The claim says A=0x6D14F0 (116B), B=0x6D1570 (tail ret @0x6D15E3), C=0x6D15F0 (27B).
My class1 capstone sweep found `call 0x6D1610` and `call 0x6D1660` from
0x4FC59F / 0x4FC1D9 -- those land in the interior of that neighbourhood.
Decode it and settle the real layout.
"""
from base import BUF, IB, u32, s32, cstr
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

lo, hi = 0x006D13E0, 0x006D1700
code = bytes(BUF[lo - IB: hi - IB])

print("=== disasm 0x%08X..0x%08X ===" % (lo, hi))
for ins in md.disasm(code, lo):
    mark = ""
    if ins.address in (0x006D14F0, 0x006D1570, 0x006D15F0):
        mark = "   <<< CLAIMED FUNCTION START"
    if ins.mnemonic == "ret" or ins.mnemonic.startswith("ret"):
        mark += "   <<< RET"
    print("%08X  %-24s %-10s %s%s" %
          (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))

print()
print("=== which addresses are called from anywhere in .text? ===")
from base import TEXT
tlo = TEXT["va"]; thi = TEXT["va"] + TEXT["vsize"]
callers = {}
for va in range(tlo, thi - 5):
    i = va - IB
    if BUF[i] in (0xE8, 0xE9):
        t = va + 5 + s32(va + 1)
        callers.setdefault(t, []).append((va, "call" if BUF[i] == 0xE8 else "jmp"))
for f in (0x006D14F0, 0x006D1570, 0x006D15F0, 0x006D1610, 0x006D1660,
          0x006D1680, 0x006D150F, 0x006D1570):
    if f in callers:
        print("  0x%08X <- %s" % (f, [("%s@%08X" % (k, a)) for a, k in callers[f]]))
    else:
        print("  0x%08X <- (no direct E8/E9 in .text)" % f)

# What is at the START of each claimed "function" and what precedes it?
print()
print("=== bytes just before each claimed start (is it preceded by padding?) ===")
for f in (0x006D14F0, 0x006D1570, 0x006D15F0, 0x006D1610, 0x006D1660):
    pre = bytes(BUF[f - IB - 16: f - IB])
    print("  0x%08X  prev16=%s" % (f, pre.hex()))

# Find all functions in this range that ARE referenced, to build the real map
print()
print("=== referenced entry points in 0x6D1000..0x6D1800 ===")
for f in sorted(callers):
    if 0x006D1000 <= f < 0x006D1800:
        print("  0x%08X  n=%d  %s" % (f, len(callers[f]),
              [("%s@%08X" % (k, a)) for a, k in callers[f]][:6]))
