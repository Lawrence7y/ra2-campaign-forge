# -*- coding: utf-8 -*-
"""R-063b probe7 (continuation): close the two open items left by probe5 crash
and probe6 broken sim. Read-only; reuses R-062/R-061 gate machinery only.

A) image sha256 self-check.
B) 24 rows (12 unknown-reg + 12 bare): row call insn bytes/mn/op/target.
C) edi provenance at 0x778ac7 (probe5 crashed before printing it) + block
   disasm 0x778ab0..0x778af0 (also covers the 0x7e1b0c store context).
D) 0x528C00 callee-side fill check: first 48 insns; every [ecx...]/[reg] imm32
   dword store in the first 200 insns; first ret (cleanup); image-wide aligned
   caller count.
E) [esp+0x20] textual write scan in whole H prefix [0x4f1ca0, 0x4f207c).
F) hop2/hop3 anchor bytes re-pin from stream (no recompute).
G) whole-function 'esi,'/'edx,' writer census for F1/F2/F3/hub windows
   (callee-saved copy uniqueness).
H) H=0x4f1ca0 head region prologue + E8 caller count (boundary note).
"""
import sys, os, re, bisect, hashlib, json

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

UR = [0x4f2ced, 0x4f2d5c, 0x4f2e30, 0x4f3219, 0x4f32a4, 0x4f32e9,
      0x4f332e, 0x4f337c, 0x4f33ca, 0x4f38f9, 0x4f39c1, 0x4f3bf3]
BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]


def show(a, b, pre="  "):
    k = bisect.bisect_left(addrs, a)
    while k < len(stream) and stream[k][0] < b:
        va, sz, bs, mn, op, t = stream[k]
        print("%s%08x: %-14s %-6s %s%s" % (pre, va, bs, mn, op,
              " ->%x" % t if t and mn in ("call", "jmp") else ""))
        k += 1


print("== A) image self-check")
h = hashlib.sha256(open(G61.EXE, "rb").read()).hexdigest()
print("  sha256 =", h)
print("  expect = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
print("  match  =", h == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")

print("\n== B) row call insns")
for c in UR + BARE:
    a, sz, bs, mn, op, t = stream[idx[c]]
    print("  row %06x: %-14s %-5s %-30s tgt=%s" % (c, bs, mn, op, hex(t) if t else "-"))

print("\n== C) edi provenance at 0x778ac7")
w = R62.nearest_writer("edi", 0x778ac7, True, 0x778a20)
print("  nearest_writer(edi)=", w and (hex(w[0]), w[1], w[2], w[3]))
if w and w[3] in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
    w2 = R62.nearest_writer(w[3], w[0], True, 0x778a20)
    print("   <-", w2 and (hex(w2[0]), w2[1], w2[2], w2[3]))
    if w2 and w2[3] in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
        w3 = R62.nearest_writer(w2[3], w2[0], True, 0x778a20)
        print("   <-", w3 and (hex(w3[0]), w3[1], w3[2], w3[3]))
print("  block disasm 0x778ab0..0x778af0:")
show(0x778ab0, 0x778af0)

print("\n== D) 0x528C00 callee-side fill check")
print("  aligned callers of 0x528c00 image-wide: %d" % len(callers.get(0x528c00, ())))
print("  first 48 insns:")
k0 = idx[0x528c00]
for j in range(k0, k0 + 48):
    a, sz, bs, mn, op, t = stream[j]
    print("   %08x: %-14s %-6s %s%s" % (a, bs, mn, op,
          " ->%x" % t if t and mn in ("call", "jmp") else ""))
print("  imm32 dword stores to [ecx]/[reg] in first 200 insns:")
cnt = 0
for j in range(k0, k0 + 200):
    a, sz, bs, mn, op, t = stream[j]
    if mn == "mov" and op.startswith("dword ptr [") and "041b7e00" in bs:
        print("   %08x %s %s %s" % (a, bs, mn, op))
        cnt += 1
print("  count:", cnt)
# any store of ANY value to [ecx] or [ecx+disp] early (constructor-style)
print("  any 'mov dword ptr [ecx' in first 40 insns:")
for j in range(k0, k0 + 40):
    a, sz, bs, mn, op, t = stream[j]
    if op.startswith("dword ptr [ecx"):
        print("   %08x %s %s %s" % (a, bs, mn, op))

print("\n== E) [esp+0x20] textual writes in [0x4f1ca0, 0x4f207c)")
n = 0
k = bisect.bisect_left(addrs, 0x4f1ca0)
while k < len(stream) and stream[k][0] < 0x4f207c:
    a, sz, bs, mn, op, t = stream[k]
    if re.match(r"^dword ptr \[esp \+ 0x20\], ", op):
        print("   %08x %s %s %s" % (a, bs, mn, op))
        n += 1
    k += 1
print("  count:", n)

print("\n== F) hop anchors re-pin (bytes from stream)")
for va in (0x4f3976, 0x4f392e, 0x4f394b, 0x4f38b8, 0x4f20b7, 0x4f207c,
           0x4f397a, 0x4f3932, 0x4f394f, 0x4f20c1, 0x778ac7, 0x778acf, 0x778ae5):
    a, sz, bs, mn, op, t = stream[idx[va]]
    print("  %08x: %-14s %-6s %s%s" % (a, bs, mn, op,
          " ->%x" % t if t and mn in ("call", "jmp") else ""))

print("\n== G) callee-saved writer census in whole function prefixes")
def reg_writers(reg, lo, hi):
    out = []
    k = bisect.bisect_left(addrs, lo)
    while k < len(stream) and stream[k][0] < hi:
        a, sz, bs, mn, op, t = stream[k]
        if mn in ("mov", "lea") and op.startswith(reg + ", "):
            out.append((hex(a), bs, mn, op))
        k += 1
    return out

for F, rows in ((0x4f2c70, [0x4f2ced, 0x4f2d5c, 0x4f2e30]),
                (0x4f3140, [0x4f3219, 0x4f32a4, 0x4f32e9, 0x4f332e, 0x4f337c, 0x4f33ca]),
                (0x4f3b80, [0x4f3bf3]),
                (0x4f38b0, [0x4f38f9, 0x4f39c1])):
    for r in rows:
        hi = r
        esi_w = reg_writers("esi", F, hi)
        edx_w = reg_writers("edx", F, hi)
        print("  F=%08x row=%06x  esi-writers=%s" % (F, r, esi_w))
        print("                 edx-writers=%s" % edx_w)

print("\n== H) H=0x4f1ca0 head + prologue + callers")
print("  E8 callers of 0x4f1ca0:", [hex(x) for x in sorted(callers.get(0x4f1ca0, ()))])
show(0x4f1ca0, 0x4f1cdd)
print("done.")
