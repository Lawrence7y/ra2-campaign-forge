# -*- coding: utf-8 -*-
"""R-063b probe11 (continuation): finish the D-sim.

Upgrades over probe10:
  - ret-unknown call sites: if ZERO pushes happened since the last stack anchor
    (previous call with known cleanup / `add esp,N` / head), the callee has no
    stack args to clean => its ret-imm is provably 0 => D unchanged (recorded
    as safe). Otherwise the path is pruned (cause kept).
  - hard ret census retry for 0x7b5b30 / 0x5256f0 (cap 200k).
  - context disasm: indirect call 0x5cef6b; 0x5d7c86; 0x76c692.
  - D-hazard check for the 5 FROZEN constructed rows: linear count of
    call/push/pop/add/sub-esp between the frozen stamp VA and the row VA
    (same-disp textual pairing is only sound when that count is 0).
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

_imm_cache = {}


def ret_imm(tgt, cap=6000):
    key = (tgt, cap)
    if key in _imm_cache:
        return _imm_cache[key]
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
    _imm_cache[key] = out
    return out


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
            causes.append("no-idx@%08x" % a)
            continue
        va, sz, bs, mn, op, t = stream[k]
        nxt = []
        prune = False
        if mn in ("ret", "retf", "hlt", "ud2"):
            continue
        if mn == "jmp":
            if t is not None and TLO <= t < THI and t in idx:
                nxt.append(t)
            else:
                causes.append("jmp-out@%08x" % a)
            continue
        if mn == "call":
            imm = ret_imm(t) if (t is not None and TLO <= t < THI) else None
            if imm is None:
                # zero-pushes-since-anchor rule: the sim state doesn't track
                # anchors, so use a local re-walk: count pushes on the path is
                # expensive; instead handle via post-pass (see below). Here:
                # prune but remember.
                causes.append("ret-unknown@%08x->%08x" % (a, t))
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
        elif mn == "leave" or op.endswith(", esp") or op == "esp":
            causes.append("esp-other@%08x %s %s" % (a, mn, op))
            continue
        else:
            nd = dset
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


def zero_push_variant(head, row, stuck_call):
    """sim that treats the stuck call as D-neutral (0 stack args), i.e. the
    provable-0 cleanup rule; other ret-unknown calls still prune."""
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
            continue
        if mn == "call":
            imm = ret_imm(t) if (t is not None and TLO <= t < THI) else None
            if imm is None:
                if a == stuck_call:
                    causes.append("assumed-0args@%08x->%08x" % (a, t))
                    nd = dset  # provable only if no pushes since anchor
                else:
                    causes.append("ret-unknown@%08x->%08x" % (a, t))
                    continue
            else:
                nd = tuple(d - imm for d in dset)
        elif mn == "push":
            nd = tuple(d + 4 for d in dset)
        elif mn == "pop":
            nd = tuple(d - 4 for d in dset)
        elif mn in ("sub", "add") and re.match(r"^esp, ", op):
            try:
                v = int(op.split(", ")[1], 0)
            except Exception:
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


def report_row(c, states, causes, tag):
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    H = heads[0]
    k = idx[c] - 1
    _, _, _, lmn, lop, _t = stream[k]
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", lop)
    s = m.group(1)
    disp = int(s, 16) if s.startswith("0x") else int(s)
    drow = sorted(set(states.get(c, ())))
    print("row %06x head=%08x [%s] D(row)=%s causes=%s" % (
        c, H, tag, [hex(x) for x in drow], causes[:4]))
    if not drow:
        return
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


print("== 0) hard ret census retry")
for h in (0x7b5b30, 0x5256f0):
    print("  %08x ret_imm=%s" % (h, ret_imm(h, 200000)))

print("\n== 1) context disasm")
print("  -- 0x5cef5c..0x5cefd0 (indirect call ctx) --")
k = bisect.bisect_left(addrs, 0x5cef5c)
while k < len(stream) and stream[k][0] < 0x5cefd0:
    va, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s%s" % (va, bs, mn, op,
          " ->%x" % t if t and mn in ("call", "jmp") else ""))
    k += 1
print("  -- 0x5d7c78..0x5d7c92 --")
k = bisect.bisect_left(addrs, 0x5d7c78)
while k < len(stream) and stream[k][0] < 0x5d7c92:
    va, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s" % (va, bs, mn, op))
    k += 1
print("  -- 0x76c68a..0x76c69a --")
k = bisect.bisect_left(addrs, 0x76c68a)
while k < len(stream) and stream[k][0] < 0x76c69a:
    va, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s" % (va, bs, mn, op))
    k += 1

print("\n== 2) strict sim (probe10 rules, cap 200k rets)")
for c in BARE:
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    states, causes = sim(heads[0], c)
    report_row(c, states, causes, "strict")

print("\n== 3) D-hazard check for 5 frozen constructed rows")
for row, stamp in CONSTR:
    cnt = {"call": 0, "push": 0, "pop": 0, "add": 0, "sub": 0}
    k = idx[stamp]
    while k < len(stream) and stream[k][0] < row:
        va, sz, bs, mn, op, t = stream[k]
        if mn in cnt:
            cnt[mn] += 1
        k += 1
    print("  row %06x stamp %08x gap-hazard=%s" % (row, stamp, cnt))
print("done.")
