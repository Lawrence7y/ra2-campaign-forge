# -*- coding: utf-8 -*-
"""R-063b probe4: resolve remaining questions with byte-level output.

Q1 full list of 45 .text insns with imm32=0x7E1B04 (form taxonomy).
Q2 0x778a20 vs 0x778ac3: true heads (E8 callers), ret-terminated frame windows,
   every write of [esp+0x34] and [esp+0x38] inside, the three witness-call sites
   with raw bytes, and whether 0x778ac3 is reachable from the E8 head 0x778a20
   (branch graph).
Q3 hub 0x4f38b0 cold-entry verification: all call/jmp insns targeting it; push
   imm32 of it; vtable-scan already 0. Epilogue pop-symmetry for F1/F2/F3/hub.
Q4 hop3/hop4: [esp+0x20]/[esp+0x18] writers in H frame (callers 0x4f3932/494f/
   4f397a and 0x4f20c1); caller count of H=0x4f1cdd head; classify_call of every
   aligned caller of 0x528c00 that lives inside H frame.
Q5 relay check: are there `mov reg,0x7e1b04` (reg dest) forms? (expect 0)
"""
import sys, os, re, struct, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G61

R62.load()
stream = R62._ctx["stream"]; idx = R62._ctx["idx"]
callers = R62._ctx["callers"]; pred = R62._ctx["pred"]
addrs = [s[0] for s in stream]
TLO, THI = R62._ctx["TLO"], G61._ctx["THI"]


def show(a, b):
    k = bisect.bisect_left(addrs, a)
    while k < len(stream) and stream[k][0] < b:
        va, sz, bs, mn, op, t = stream[k]
        print("  %08x: %-14s %-6s %s%s" % (va, bs, mn, op,
              " ->%x" % t if t and mn in ("call", "jmp") else ""))
        k += 1


def breach(site):
    seen = {site}; work = [site]
    while work:
        a = work.pop()
        for p in pred.get(a, ()):
            if p not in seen: seen.add(p); work.append(p)
    seen.discard(site); return seen


E8T = set(callers)

print("== Q1: every .text insn whose bytes contain 041b7e00")
c = 0
for a, sz, bs, mn, op, t in stream:
    if "041b7e00" in bs:
        c += 1
        form = "mem-store" if op.startswith("dword ptr [") else mn + " " + op
        print("  %08x %-14s %s %s | %s" % (a, bs, mn, op, form))
print("  total:", c)

print("\n== Q2: windows and heads")
for h in (0x778a20, 0x778ac3):
    print("  head? %08x E8-callers=%s reach-from-778a20: %s" % (
        h, [hex(x) for x in sorted(callers.get(h, []))],
        (0x778ac3 in breach(0x778ac3) ) if False else (0x778ac3 in fwd if False else "?")))
F = fwd = None
# reachability of 0x778ac3 region from 0x778a20: forward closure
def fwdr(head):
    seen = set(); work = [head]
    while work:
        a = work.pop()
        k = idx.get(a)
        if k is None: continue
        a2, sz, bs, mn, op, t = stream[k]
        if mn in ("ret", "retf", "hlt", "ud2"): continue
        if t is not None and TLO <= t < THI and mn == "jmp" and t not in seen:
            seen.add(t); work.append(t)
        if mn.startswith("j") and mn != "jmp" and t is not None and TLO <= t < THI and t not in seen:
            seen.add(t); work.append(t)
        n = a2 + sz
        if mn != "jmp" and n < THI and n not in seen:
            seen.add(n); work.append(n)
    return seen
fw = fwdr(0x778a20)
print("  0x778ac3 in fwd(0x778a20): %s ; 0x778bcb in fwd: %s" % (0x778ac3 in fw, 0x778bcb in fw))
# E8-heads that reach 0x778ac3
b3 = breach(0x778ac3) & E8T
print("  E8 heads reaching 0x778ac3: %s" % [hex(x) for x in sorted(b3)])
# slot scans over [0x778a20, 0x778e60)
def slot_scan(lo, hi, pat):
    out = []
    k = bisect.bisect_left(addrs, lo)
    while k < len(stream) and stream[k][0] < hi:
        a, sz, bs, mn, op, t = stream[k]
        if re.search(pat, op): out.append((hex(a), bs, mn, op))
        k += 1
    return out
print("  writes/read [esp+0x38] in [778a20,778e60):")
for x in slot_scan(0x778a20, 0x778e60, r"esp \+ 0x38\]"):
    print("    ", x)
print("  [esp+0x34] writes in [778a20,778e60):")
for x in slot_scan(0x778a20, 0x778e60, r"esp \+ 0x34\]"):
    if x[2] == "mov" and x[3].startswith("dword"):
        print("    ", x)
print("  witness call sites raw:")
show(0x778bc5, 0x778bd3); show(0x778dc5, 0x778dd5); show(0x778e18, 0x778e28)

print("\n== Q3: hub inbound + epilogues")
for t in (0x4f38b0,):
    ins = [(hex(a), mn, bs) for a, sz, bs, mn, op, tg in stream if tg == t and mn in ("call", "jmp") or (mn.startswith("j") and tg == t)]
    print("  branches targeting %08x: %s" % (t, ins))
    # push imm
    hits = [hex(a) for a, sz, bs, mn, op, tg in stream if mn == "push" and op == "0x4f38b0"]
    print("  push imm32 refs: %s" % hits)
for h, epi in ((0x4f2c70, (0x4f2f80, 0x4f3140)), (0x4f3140, (0x4f3830, 0x4f38b0)),
               (0x4f3b80, (0x4f3b80, 0x4f38b0 + 0x1000)), (0x4f38b0, (0x4f3a2e, 0x4f3a4a))):
    if h == 0x4f3b80:
        continue
    pops = [(hex(a), mn, op) for a, sz, bs, mn, op, t in stream if epi[0] <= a < epi[1] and mn in ("pop", "ret")]
    print("  tail-region pop/ret %08x..%08x (for head %08x): %s" % (epi[0], epi[1], h, pops))
pops3b = [(hex(a), mn, op) for a, sz, bs, mn, op, t in stream if 0x4f3b80 <= a < 0x4f3c40 and mn in ("pop",)]
print("  0x4f3b80 pops:", pops3b)

print("\n== Q4: hop3/4")
for g, slot in ((0x4f3932, "0x20"), (0x4f394f, "0x20"), (0x4f397a, "0x20"), (0x4f20c1, "0x20"), (0x4f20c1, "0x18")):
    wr = R62.slot_writers(slot, g)
    print("  writers of [esp+%s] before %08x: %s" % (slot, g, [(hex(x[0]), x[1]) for x in wr]))
H = 0x4f1cdd
print("  H head? E8-callers of %08x: %s" % (H, [hex(x) for x in sorted(callers.get(H, []))]))
bH = breach(H) & E8T
print("  heads reaching H: %s" % [hex(x) for x in sorted(bH)])
print("  classify every aligned caller of 0x528c00 with frame_lo==%08x:" % H)
for cc in sorted(callers.get(0x528c00, [])):
    if R62.frame_lo(cc) == H:
        v, ch = R62.classify_call(cc)
        print("    %08x %s %s" % (cc, v, ch))
print("  prologue of H region:")
show(0x4f1cdd, 0x4f1cff)
print("  frame_lo(0x4f20c1)=%08x" % R62.frame_lo(0x4f20c1))

print("\n== Q5: reg-dest imm forms")
c = [(hex(a), mn, op) for a, sz, bs, mn, op, t in stream if "7e1b04" in op and not op.startswith("dword ptr [")]
print("  non-mem-store mentions:", c)
print("== epilogue pop symmetry F1/F2")
for lo, hi in ((0x4f2f00, 0x4f2c70),):
    pass
for h, hi in ((0x4f2c70, 0x4f2f60), (0x4f3140, 0x4f37a0), (0x4f3b80, 0x4f3c60), (0x4f38b0, 0x4f3a4a)):
    pops = [(hex(a), bs, op) for a, sz, bs, mn, op, t in stream
            if h <= a < hi and mn == "pop" and op in ("ebx", "esi", "edi", "ebp")]
    rets = [(hex(a), bs, op) for a, sz, bs, mn, op, t in stream if h <= a < hi and mn == "ret"]
    print("  head %08x pops=%s rets=%s" % (h, pops, rets))
