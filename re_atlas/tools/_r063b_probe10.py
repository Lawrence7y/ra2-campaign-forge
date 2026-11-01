# -*- coding: utf-8 -*-
"""R-063b probe10 (continuation): exact path-sensitive esp-delta (D) abstract
interpretation for the 12 bare witness rows.

Fixes probe6's two defects (witness-lea regex never matched; callee ret-cleanup
unknown) and probe5's KeyError (decode gap). Method:
  - D relative to esp0 = esp right after the head's frame-establishing insns
    (sim starts at the E8 head with D=0; push/pop/sub/add esp and call ret-imm
    are the only D-movers; any other esp-affecting insn => that path is
    marked unresolved).
  - forward DFS head->row over the gate stream with memo (addr -> set of D);
    paths through `ret` are pruned (a ret leaves the frame, cannot reach the
    row); jcc explores both arms; memo caps state explosion.
  - callee ret-imm extracted once per callee (first linear ret, jmp-chains
    followed); ret-unknown calls mark their path unresolved (recorded).
  - witness cell W = lea_disp - D(at lea). Every on-path store whose
    P = disp - D equals W is reported with its stored operand. P<0 (push zone)
    is out of local scope; a P>=0 store from a reg gets a one-hop provenance
    note (xor/mov imm) when trivially available.
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

BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]

_imm_cache = {}


def ret_imm(tgt):
    if tgt in _imm_cache:
        return _imm_cache[tgt]
    out = None
    j = bisect.bisect_left(addrs, tgt)
    if j < len(stream) and stream[j][0] == tgt:
        for _ in range(6000):
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
    _imm_cache[tgt] = out
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
    """returns (Dsets dict addr->set, unresolved_causes list)."""
    causes = []
    states = {head: (0,)}
    order = [head]
    steps = 0
    k0 = idx[head]
    while order:
        steps += 1
        if steps > 400000:
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
            continue  # frame exit: prune
        if mn == "jmp":
            if t is not None and TLO <= t < THI and t in idx:
                nxt.append(t)
            else:
                causes.append("jmp-out@%08x" % a)
            continue
        if mn == "call":
            if t is not None and TLO <= t < THI:
                imm = ret_imm(t)
                if imm is None:
                    causes.append("ret-unknown@%08x->%08x" % (a, t))
                    continue
                nd = tuple(d - imm for d in dset)
            else:
                causes.append("call-indirect@%08x" % a)
                continue
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
        elif mn in ("leave",) or "esp" in op.split(",")[0:1] or op.endswith(", esp") or op == "esp, esp":
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


for c in BARE:
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    H = heads[0]
    k = idx[c] - 1
    _, _, _, lmn, lop, _t = stream[k]
    disp = None
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", lop)
    if m:
        s = m.group(1)
        disp = int(s, 16) if s.startswith("0x") else int(s)
    states, causes = sim(H, c)
    drow = states.get(c, ())
    print("row %06x head=%08x lea=%s disp=%s D(row)=%s" % (
        c, H, hex(stream[k][0]), hex(disp) if disp is not None else "?",
        [hex(x) for x in sorted(drow)]))
    if not drow or disp is None:
        print("   UNRESOLVED causes:", causes[:10])
        continue
    for D in sorted(set(drow)):
        W = disp - D
        print("   D=%s -> witness phys cell W=0x%x" % (hex(D), W))
        # collect stores on reachable path with P == W
        hits = []
        for a2, dsets in states.items():
            for D2 in dsets:
                kk = idx[a2]
                va2, sz2, bs2, mn2, op2, t2 = stream[kk]
                if mn2 == "mov" and op2.startswith("dword ptr [esp"):
                    m2 = re.search(r"esp \+ (0x[0-9a-f]+|\d+)\]", op2)
                    if m2:
                        s2 = m2.group(1)
                        x2 = int(s2, 16) if s2.startswith("0x") else int(s2)
                        if x2 - D2 == W:
                            hits.append((hex(a2), bs2, op2, hex(D2)))
        if hits:
            for h2 in hits:
                print("      store@%s %s %s (D=%s)" % h2)
        else:
            print("      (no on-path store of cell 0x%x)" % W)
    if causes:
        print("   causes (non-fatal, pruned paths):", causes[:6])
print("done.")
