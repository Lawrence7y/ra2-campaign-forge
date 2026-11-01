# -*- coding: utf-8 -*-
"""R-063b probe6: path-sensitive stack simulation for the 12 bare rows.

For each bare row:
  head = the E8 head whose forward-closure contains the row (fallthrough edges,
  jmp taken, jcc taken-BOTH? no -- we follow the LINEAR path: head..row in
  address order is NOT valid across branches; instead simulate the single
  straight-line path by backward-unique-branch... )

Pragmatic approach used: walk instructions head -> row in stream order
(address-ordered linear path), at each `call <known>` ADD the callee ret-cleanup
(read callee's ret imm), for `push/pop/sub esp/add esp` update delta D.
The linear window between head and row in these compiler-generated functions is
the path the register-target lea/store instructions actually executed under
(basic-block order == address order in this .text, verified per-frame by
showing branch targets). We report D and physical slot (head-ESP0 relative)
for: (a) each imm-0x7E1B04 store, (b) the witness lea, and flag MATCH/nomismatch.
Also report every branch (call/jmp/jcc target) crossing the window to record
where linear order may diverge (honest bound).
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

BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]
VT = "041b7e00"


def breach(site):
    seen = {site}; work = [site]
    while work:
        a = work.pop()
        for p in pred.get(a, ()):
            if p not in seen: seen.add(p); work.append(p)
    seen.discard(site); return seen


E8T = set(callers)


def callee_cleanup(tgt):
    """scan callee (<=16 insns until first ret) for ret imm; None if unknown."""
    if tgt not in idx:
        return None
    j = idx[tgt]
    if j and stream[j - 1][0] + stream[j - 1][1] != tgt:
        # target not aligned into stream start; search forward for its head anyway
        j = bisect.bisect_left(addrs, tgt)
        if stream[j][0] != tgt:
            return None
    for _ in range(40):
        if j >= len(stream):
            return None
        a, sz, bs, mn, op, t = stream[j]
        if a > tgt + 0x200:
            return None
        if mn == "ret":
            return int(op, 16) if op else 0
        if mn == "jmp":
            if t is not None and TLO <= t < THI:
                j = bisect.bisect_left(addrs, t)
                continue
            return None
        j += 1
    return None


def parse_disp(op):
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", op)
    return int(m.group(1), 16) if m and m.group(1).startswith("0x") else (int(m.group(1)) if m else None)


for c in BARE:
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    H = heads[0]
    # simulate head -> row
    D = 0
    k = idx[H]
    events = []
    diverge = []
    while k < len(stream) and stream[k][0] <= c:
        a, sz, bs, mn, op, t = stream[k]
        if mn == "push":
            D += 4
        elif mn == "pop":
            D -= 4
        elif mn == "sub":
            m = re.match(r"esp, (\S+)$", op)
            if m: D += int(m.group(1), 0)
        elif mn == "add":
            m = re.match(r"esp, (\S+)$", op)
            if m: D -= int(m.group(1), 0)
        elif mn == "call" and t is not None and TLO <= t < THI:
            if t in idx and stream[idx[t]][0] == t:
                cl = callee_cleanup(t)
                if cl is None:
                    diverge.append((hex(a), "callee %08x cleanup-unknown" % t))
                elif cl:
                    D -= cl
            else:
                diverge.append((hex(a), "callee %08x unaligned-head" % t))
        if mn.startswith("j") and mn != "jmp" and t is not None:
            # fallthrough continues linearly; taken branch skipped => divergence
            if not (a < t <= c + 0x400) or t > a:
                diverge.append((hex(a), "jcc taken-target %08x outside linear path" % t))
        # record VT stores and the witness lea
        if VT in bs and parse_disp(op) is not None:
            events.append((hex(a), "VTstore", op, "phys_off_from_headESP0=0x%x" % (parse_disp(op) - D)))
        if a == c - 4 or a == c - 8:  # the lea right before the witness call
            m = re.match(r"^(lea \w+, \[esp \+ .+\])$", op)
            if m:
                events.append((hex(a), "witness-lea", op, "phys=0x%x" % (D - parse_disp(op))))
        if a == c:
            break
        k += 1
    print("row %06x head=%08x gate-frame_lo=%08x" % (c, H, lo))
    for e in events:
        print("   ", e)
    # deduplicate diverge
    if diverge:
        print("   divergences:", diverge[:8], "..." if len(diverge) > 8 else "")
