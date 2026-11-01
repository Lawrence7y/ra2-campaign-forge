# -*- coding: utf-8 -*-
"""R-063b probe12 (continuation): calibration + final D-sim run.

0) context: all rets inside [0x528c00, 0x529160) with imms; epilogue pops
   around 0x528dbd; ret census of 0x7b6290; 0x528c00 head pushes.
1) per-call-site overrides (each with its proof note):
     0x5cef6b -> 4   (call [eax+8] with 1 push; same-disp [esp+0x68] reload
                      at 0x5cef6e proves stack restored by callee)
     0x5cef78 -> 4   (call [edx+0x1c] with 1 push; same-disp reload 0x5cef7b)
     0x778b47 -> 0   (zero pushes since last anchor => ret-imm provably 0)
     0x5d7c86 -> 0   (zero pushes since anchor: pop edi/ebp then lea, call)
     0x76c692 -> 0   (zero pushes since anchor: lea then call)
     0x5cefb7 -> censused ret-imm of 0x7b6290 if found
2) final sim run over the 12 bare rows with overrides.
Read-only.
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

BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]
OVR = {0x5cef6b: (4, "same-disp-reload"), 0x5cef78: (4, "same-disp-reload"),
       0x778b47: (0, "zero-args"), 0x5d7c86: (0, "zero-args"),
       0x76c692: (0, "zero-args")}


def show(a, b):
    k = bisect.bisect_left(addrs, a)
    while k < len(stream) and stream[k][0] < b:
        va, sz, bs, mn, op, t = stream[k]
        print("   %08x: %-14s %-6s %s%s" % (va, bs, mn, op,
              " ->%x" % t if t and mn in ("call", "jmp") else ""))
        k += 1


def ret_imm(tgt, cap=200000):
    out = None
    j = bisect.bisect_left(addrs, tgt)
    if j < len(stream) and stream[j][0] == tgt:
        for _ in range(cap):
            if j >= len(stream):
                break
            a, sz, bs, mn, op, t = stream[j]
            if mn == "ret":
                out = int(op, 16) if op else 0
                break
            if mn == "jmp" and t is not None and TLO <= t < THI:
                j2 = bisect.bisect_left(addrs, t)
                if j2 < len(stream) and stream[j2][0] == t:
                    j = j2
                    continue
                break
            if mn in ("retf", "hlt", "ud2", "x87-boundary"):
                break
            j += 1
    return out


print("== 0) calibration")
rets = []
k = bisect.bisect_left(addrs, 0x528c00)
while k < len(stream) and stream[k][0] < 0x529160:
    va, sz, bs, mn, op, t = stream[k]
    if mn == "ret":
        rets.append((hex(va), bs, op))
    k += 1
print("  rets in [0x528c00,0x529160):", rets)
print("  0x7b6290 ret_imm:", ret_imm(0x7b6290))
print("  epilogue context 0x528da8..0x528dc8:")
show(0x528da8, 0x528dc8)
print("  0x528c00 head pushes:")
show(0x528c00, 0x528c14)
print("  0x7b6290 head:")
show(0x7b6290, 0x7b62a8)

OVR[0x5cefb7] = None  # placeholder; filled after census below
r = ret_imm(0x7b6290)
if r is not None:
    OVR[0x5cefb7] = (r, "census")

print("\n== 2) final sim")


def breach(site):
    seen = {site}
    work = [site]
    while work:
        a = work.pop()
        for p in pred.get(a, ()):
            if p not in seen:
                seen.add(p)
                work.append(p)
    seen.discard(site)
    return seen


E8T = set(callers)


def sim(head, row):
    causes = []
    states = {head: (0,)}
    order = [head]
    steps = 0
    while order:
        steps += 1
        if steps > 600000:
            causes.append("step-cap")
            break
        a = order.pop()
        dset = states[a]
        k = idx.get(a)
        if k is None:
            continue
        va, sz, bs, mn, op, t = stream[k]
        nxt = []
        if mn in ("ret", "retf", "hlt", "ud2"):
            continue
        if mn == "jmp":
            if t is not None and TLO <= t < THI and t in idx:
                nxt.append(t)
            else:
                causes.append("jmp-out@%08x" % a)
            continue
        if mn == "call":
            if a in OVR and OVR[a] is not None:
                imm, why = OVR[a]
                nd = tuple(d - imm for d in dset)
            elif a in OVR:
                causes.append("ovr-none@%08x" % a)
                continue
            else:
                imm = ret_imm(t) if (t is not None and TLO <= t < THI) else None
                if imm is None:
                    causes.append("ret-unknown@%08x->%s" % (
                        a, hex(t) if t else "indirect"))
                    continue
                nd = tuple(d - imm for d in dset)
        elif mn == "push":
            nd = tuple(d + 4 for d in dset)
        elif mn == "pop":
            nd = tuple(d - 4 for d in dset)
        elif mn in ("sub", "add") and re.match(r"^esp, ", op):
            try:
                v = int(op.split(", ")[1], 0)
            except Exception:
                causes.append("esp-op-unparsed@%08x" % a)
                continue
            nd = tuple(d + v if mn == "sub" else d - v for d in dset)
        elif mn.startswith("j"):
            nf = va + sz
            if nf in idx:
                nxt.append(nf)
            if t is not None and TLO <= t < THI and t in idx:
                nxt.append(t)
            nd = dset
        elif mn == "leave" or op.endswith(", esp"):
            causes.append("esp-other@%08x" % a)
            continue
        else:
            nd = dset
        nf = va + sz
        succs = nxt if nxt else ([nf] if nf in idx else [])
        for s in succs:
            merged = set(states.get(s, ())) | set(nd)
            if len(merged) > 8:
                causes.append("D-ambig@%08x" % s)
                continue
            if s not in states or set(states[s]) != merged:
                states[s] = tuple(sorted(merged))
                if s not in order:
                    order.append(s)
            else:
                states[s] = tuple(sorted(merged))
    return states, causes


for c in BARE:
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    H = heads[0]
    k = idx[c] - 1
    _, _, _, lmn, lop, _t = stream[k]
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", lop)
    s = m.group(1)
    disp = int(s, 16) if s.startswith("0x") else int(s)
    states, causes = sim(H, c)
    drow = sorted(set(states.get(c, ())))
    print("row %06x head=%08x D(row)=%s causes=%s" % (
        c, H, [hex(x) for x in drow], causes[:5]))
    for D in drow:
        W = disp - D
        print("   D=%s W=0x%x" % (hex(D), W))
        hits = []
        for a2, dsets in states.items():
            kk = idx[a2]
            va2, sz2, bs2, mn2, op2, t2 = stream[kk]
            if mn2 == "mov" and op2.startswith("dword ptr [esp"):
                m2 = re.search(r"esp \+ (0x[0-9a-f]+|\d+)\]", op2)
                if m2:
                    s2 = m2.group(1)
                    x2 = int(s2, 16) if s2.startswith("0x") else int(s2)
                    for D2 in dsets:
                        if x2 - D2 == W:
                            hits.append((hex(a2), bs2, op2, hex(D2)))
        for h2 in sorted(set(hits)):
            print("      store@%s %s %s (D=%s)" % h2)
        if not hits:
            print("      (no on-path store of cell)")
print("done.")
