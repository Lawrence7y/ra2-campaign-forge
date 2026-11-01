# -*- coding: utf-8 -*-
"""R-063b probe14 (continuation, FINAL): corrected esp-handling sim + full
cell-accounting for all 17 stack-object rows.

Fixes vs probe12/13:
  - esp-PRESERVING insns (mov reg, esp / mov [mem], esp) are D-neutral, NOT
    pruned (probe12 wrongly pruned them: silent empty-cause death of 5d76a9);
  - esp-WRITING insns (mov esp, ... / xchg / leave / pop esp) prune with cause.

Outputs per row (12 bare + 5 frozen-constructed):
  D(row) set; witness cell W; ALL on-path stores hitting W (value+site);
  for the 5 constructed rows additionally: which leas/calls consume the frozen
  stamp cell P(stamp) (who really eats the 0x7E1B04 stamp).
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
CONSTR = [(0x77884f, 0x7787c0), (0x77890c, 0x7787c0), (0x778956, 0x7787c0),
          (0x779c3d, 0x779bb3), (0x779ebd, 0x779e33)]
OVR = {0x5cef6b: (4, "same-disp-reload"), 0x5cef78: (4, "same-disp-reload"),
       0x778b47: (0, "zero-args"), 0x5d7c86: (0, "zero-args"),
       0x76c692: (0, "zero-args"), 0x5cefb7: (0, "census-ret0")}


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


def ret_imm(tgt):
    j = bisect.bisect_left(addrs, tgt)
    if j >= len(stream) or stream[j][0] != tgt:
        return None
    for _ in range(200000):
        if j >= len(stream):
            return None
        a, sz, bs, mn, op, t = stream[j]
        if mn == "ret":
            return int(op, 16) if op else 0
        if mn == "jmp" and t is not None and TLO <= t < THI:
            j2 = bisect.bisect_left(addrs, t)
            if j2 < len(stream) and stream[j2][0] == t:
                j = j2
                continue
            return None
        if mn in ("retf", "hlt", "ud2", "x87-boundary"):
            return None
        j += 1
    return None


def sim(head):
    causes = []
    states = {head: (0,)}
    order = [head]
    steps = 0
    while order:
        steps += 1
        if steps > 800000:
            causes.append("step-cap")
            break
        a = order.pop()
        dset = states[a]
        k = idx.get(a)
        if k is None:
            causes.append("no-idx@%08x" % a)
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
            if a in OVR:
                imm = OVR[a][0]
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
        elif mn == "leave" or mn == "pop" or op.startswith("esp,") or \
                (mn in ("mov", "xchg") and op.split(",")[0].strip() == "esp"):
            causes.append("esp-write@%08x %s %s" % (a, mn, op))
            continue
        else:
            nd = dset  # esp-preserving: mov reg, esp / mov [m], esp are neutral
        nf = va + sz
        succs = nxt if nxt else ([nf] if nf in idx else [])
        for s in succs:
            merged = set(states.get(s, ())) | set(nd)
            if len(merged) > 8:
                causes.append("D-ambig@%08x n=%d" % (s, len(merged)))
                continue
            if s not in states or set(states[s]) != merged:
                states[s] = tuple(sorted(merged))
                if s not in order:
                    order.append(s)
            else:
                states[s] = tuple(sorted(merged))
    return states, causes


def cell_stores(states, W):
    hits = []
    for a2, dsets in states.items():
        kk = idx.get(a2)
        if kk is None:
            continue
        va2, sz2, bs2, mn2, op2, t2 = stream[kk]
        if mn2 == "mov" and op2.startswith("dword ptr [esp"):
            m2 = re.search(r"esp \+ (0x[0-9a-f]+|\d+)\]", op2)
            if m2:
                s2 = m2.group(1)
                x2 = int(s2, 16) if s2.startswith("0x") else int(s2)
                for D2 in dsets:
                    if x2 - D2 == W:
                        hits.append((hex(a2), bs2, op2, hex(D2)))
    return sorted(set(hits))


def cell_leas(states, W):
    hits = []
    for a2, dsets in states.items():
        kk = idx.get(a2)
        if kk is None:
            continue
        va2, sz2, bs2, mn2, op2, t2 = stream[kk]
        if mn2 == "lea":
            m2 = re.search(r"esp \+ (0x[0-9a-f]+|\d+)\]", op2)
            if m2:
                s2 = m2.group(1)
                x2 = int(s2, 16) if s2.startswith("0x") else int(s2)
                for D2 in dsets:
                    if x2 - D2 == W:
                        hits.append((hex(a2), op2, hex(D2),
                                     hex(t2) if t2 else ""))
    return sorted(set(hits))


def row_report(row, states, causes, tag):
    heads = sorted(breach(row) & E8T)
    H = heads[0]
    k = idx[row] - 1
    _, _, _, _, lop, _t = stream[k]
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", lop)
    s = m.group(1)
    disp = int(s, 16) if s.startswith("0x") else int(s)
    drow = sorted(set(states.get(row, ())))
    print("row %06x head=%08x [%s] lea-disp=%s D(row)=%s causes=%s" % (
        row, H, tag, hex(disp), [hex(x) for x in drow], causes[:4]))
    if not drow:
        return None
    out = []
    for D in drow:
        W = disp - D
        print("   D=%s W=0x%x" % (hex(D), W))
        hs = cell_stores(states, W)
        for h2 in hs:
            print("      store@%s %s %s (D=%s)" % h2)
        if not hs:
            print("      (no on-path store of cell)")
        out.append((D, W, hs))
    return out


print("== A) 12 bare rows (corrected sim)")
res_bare = {}
for c in BARE:
    heads = sorted(breach(c) & E8T)
    states, causes = sim(heads[0])
    res_bare[c] = row_report(c, states, causes, "bare")

print("\n== B) 5 frozen-constructed rows (corrected sim + full cell account)")
for row, stamp in CONSTR:
    heads = sorted(breach(row) & E8T)
    states, causes = sim(heads[0])
    out = row_report(row, states, causes, "constr")
    _, _, _, smn, sop, _ = stream[idx[stamp]]
    ms = re.search(r"esp \+ (0x[0-9a-f]+|\d+)\]", sop)
    sd = int(ms.group(1), 16) if ms.group(1).startswith("0x") else int(ms.group(1))
    ds = sorted(set(states.get(stamp, ())))
    for Ds in ds:
        P = sd - Ds
        print("   frozen-stamp %08x D=%s P=0x%x ; leas consuming P:" % (
            stamp, hex(Ds), P))
        for l in cell_leas(states, P)[:6]:
            print("      lea@%s %s (D=%s) tgt=%s" % l)
print("done.")
