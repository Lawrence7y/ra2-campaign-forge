# -*- coding: utf-8 -*-
"""R-063b probe8 (continuation): residual pins for the report.

1) G.SMALL host list; membership of 0x528c00 / 0x527f20.
2) 0x527f20 first 20 insns (does it consume this+4/+8 like 0x528c00? any
   imm32 VT store inside its range per image census).
3) 0x778a20 prologue (first 12 insns).
4) flow between the 0x778abb block and the witness block: disasm
   0x778af2..0x778bd0; bytes of jcc 0x778a8f; bytes at 0x778b9c (ret?).
5) 0x4f1c53 (H's unique caller) insn bytes.
6) witness-lea adjacency bytes for all 12 bare rows (raw 8 bytes before call).
7) 5 constructed rows' call targets (contrast, from frozen R-062 set).
"""
import sys, os, re, bisect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G61

R62.load()
stream = R62._ctx["stream"]
idx = R62._ctx["idx"]
callers = R62._ctx["callers"]
addrs = [s[0] for s in stream]

BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]
CONSTR = [0x77884f, 0x77890c, 0x778956, 0x779c3d, 0x779ebd]

print("== 1) SMALL hosts")
print("  SMALL =", [hex(x) for x in sorted(G61.SMALL)])
for h in (0x528c00, 0x527f20):
    print("  %08x in SMALL: %s ; aligned callers: %d" % (h, h in G61.SMALL,
          len(callers.get(h, ()))))

print("\n== 2) 0x527f20 first 20 insns")
k0 = idx[0x527f20]
for j in range(k0, k0 + 20):
    a, sz, bs, mn, op, t = stream[j]
    print("   %08x: %-14s %-6s %s%s" % (a, bs, mn, op,
          " ->%x" % t if t and mn in ("call", "jmp") else ""))
# [ebp+4]/[ebp+8] reads (this+4/this+8 consumption) in first 120 insns
print("  [ebp+X] reads in first 120 insns:")
for j in range(k0, k0 + 120):
    a, sz, bs, mn, op, t = stream[j]
    if "[ebp +" in op:
        print("   %08x %s %s %s" % (a, bs, mn, op))

print("\n== 3) 0x778a20 prologue")
k0 = idx[0x778a20]
for j in range(k0, k0 + 12):
    a, sz, bs, mn, op, t = stream[j]
    print("   %08x: %-14s %-6s %s" % (a, bs, mn, op))

print("\n== 4) flow 0x778af2..0x778bd0 + key jcc/ret bytes")
k = bisect.bisect_left(addrs, 0x778af2)
while k < len(stream) and stream[k][0] < 0x778bd0:
    a, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s%s" % (a, bs, mn, op,
          " ->%x" % t if t and mn in ("call", "jmp") else ""))
    k += 1
print("  jcc 0x778a8f:")
for va in (0x778a8f,):
    a, sz, bs, mn, op, t = stream[idx[va]]
    print("   %08x %s %s %s ->%x" % (a, bs, mn, op, t if t else 0))
print("  insns at 0x778b96..0x778ba4:")
k = bisect.bisect_left(addrs, 0x778b96)
while k < len(stream) and stream[k][0] < 0x778ba4:
    a, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s" % (a, bs, mn, op))
    k += 1

print("\n== 5) H caller 0x4f1c53")
a, sz, bs, mn, op, t = stream[idx[0x4f1c53]]
print("   %08x %s %s %s ->%x" % (a, bs, mn, op, t if t else 0))
k = bisect.bisect_left(addrs, 0x4f1c40)
while k < len(stream) and stream[k][0] < 0x4f1c60:
    a, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s" % (a, bs, mn, op))
    k += 1

print("\n== 6) witness-lea adjacency (8 bytes before each bare row)")
for c in BARE:
    j = idx[c]
    seg = []
    q = j - 3
    while q < j:
        a, sz, bs, mn, op, t = stream[q]
        seg.append("%08x:%s(%s %s)" % (a, bs, mn, op))
        q += 1
    print("  row %06x: %s" % (c, " | ".join(seg)))

print("\n== 7) constructed rows call targets")
for c in CONSTR:
    a, sz, bs, mn, op, t = stream[idx[c]]
    print("  row %06x: %s %s %s ->%x" % (c, bs, mn, op, t if t else 0))
print("done.")
