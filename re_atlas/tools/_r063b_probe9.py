# -*- coding: utf-8 -*-
"""R-063b probe9 (continuation, final pins for the honest account).

1) ret-imm (calling convention) of 0x528c00 / 0x527f20 and of every callee on
   the 0x778a20 witness path (first linear ret; jmp-chains followed).
2) witness-block head 0x778b9f and 0x778abb: predecessor sets from the gate
   pred graph (path uniqueness).
3) disasm continuation between witness rows: 0x778bd3..0x778dd1 and
   0x778dd5..0x778e28 (caller-side add esp cleanups + arg pushes).
4) disasm 0x778a44..0x778a95 (path from prologue to jne 0x778a8f, incl. any
   other edi writes).
Read-only; gate machinery only.
"""
import sys, os, re, bisect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G61

R62.load()
stream = R62._ctx["stream"]
idx = R62._ctx["idx"]
callers = R62._ctx["callers"]
pred = R62._ctx["pred"]
addrs = [s[0] for s in stream]
TLO, THI = R62._ctx["TLO"], G61._ctx["THI"]


def show(a, b):
    k = bisect.bisect_left(addrs, a)
    while k < len(stream) and stream[k][0] < b:
        va, sz, bs, mn, op, t = stream[k]
        print("   %08x: %-14s %-6s %s%s" % (va, bs, mn, op,
              " ->%x" % t if t and mn in ("call", "jmp") else ""))
        k += 1


def ret_imm(tgt):
    """first linear ret of callee tgt (follow jmp chains); None if unknown."""
    j = bisect.bisect_left(addrs, tgt)
    if j >= len(stream) or stream[j][0] != tgt:
        return None, "unaligned"
    for _ in range(4000):
        if j >= len(stream):
            return None, "eof"
        a, sz, bs, mn, op, t = stream[j]
        if mn == "ret":
            return (int(op, 16) if op else 0), "ret@%08x" % a
        if mn == "jmp" and t is not None and TLO <= t < THI:
            j = bisect.bisect_left(addrs, t)
            if j >= len(stream) or stream[j][0] != t:
                return None, "jmp-desync"
            continue
        if mn in ("retf", "hlt", "ud2"):
            return None, mn
        j += 1
    return None, "too-long"


print("== 1) ret-imm census")
for h in (0x528c00, 0x527f20, 0x47a9d0, 0x40e320, 0x40e340, 0x525a10,
          0x4325c0, 0x7b4690, 0x7b5b30, 0x7b5440, 0x526810, 0x778710,
          0x7b46f0, 0x5256f0, 0x431b80, 0x7b4620, 0x7b4630):
    imm, why = ret_imm(h)
    print("   %08x ret_imm=%s (%s)" % (h, imm, why))

print("\n== 2) predecessors of path joins")
for t in (0x778abb, 0x778b9f, 0x778bcf, 0x778dd1, 0x778e24, 0x778ac3):
    ps = sorted(x for x in pred.get(t, ()) )
    print("   pred(%08x) = %s" % (t, [hex(x) for x in ps]))

print("\n== 3) disasm 0x778a44..0x778a95")
show(0x778a44, 0x778a95)
print("   -- between rows --")
show(0x778bd3, 0x778dd1)
print("   --")
show(0x778dd5, 0x778e28)
print("done.")
