# -*- coding: utf-8 -*-
"""R-063b probe5: esp-delta physical slot normalization + host-side fill check.

1) walk F=0x778a20 simulating esp delta (push/pop/sub/add), report physical
   frame slot (head-relative) of: 0x778ac7 store, 0x778ae5 VT store, and the
   three witness leas 0x778bcb/0x778dcd/0x778e20; also edi provenance at ac7.
2) same for every bare row: physical slot of the witness lea; then check every
   of the 45 imm-0x7E1B04 stores if its head-relative physical slot == that one.
3) host 0x528C00 body: first bytes + any `mov [ecx], imm32` stores (callee-side
   vptr fill candidates).
"""
import sys, os, re, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G61

R62.load()
stream = R62._ctx["stream"]; idx = R62._ctx["idx"]
callers = R62._ctx["callers"]; addrs = [s[0] for s in stream]

BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]
VT_SITES = [0x40dfe9, 0x40e099, 0x40e149, 0x40e1f9, 0x40e2a9, 0x40e3e6, 0x40e4c6,
            0x49b3bd, 0x49da8d, 0x49e907, 0x4f1c05, 0x52571e, 0x52ac1a, 0x52ad07,
            0x52af77, 0x52afc6, 0x535acd, 0x535b5d, 0x54518c, 0x5977cb, 0x597a92,
            0x597de5, 0x5b3b2b, 0x5b46e6, 0x5c1344, 0x5d67fa, 0x5e5290, 0x5e65a2,
            0x668a9d, 0x764a6f, 0x76504f, 0x765200, 0x76544f, 0x7787c0, 0x778ae5,
            0x77979e, 0x7798a8, 0x7799ae, 0x779ab8, 0x779bb3, 0x779d08, 0x779e33,
            0x779f88, 0x77a16c, 0x788243]


def frame_head_frame_lo(head):
    return head


def delta_walk(head, until_va):
    """returns dict insn_va -> esp delta (bytes below head-esp) at that insn.
    delta recorded AT the insn (before its own effect) plus at insn+size."""
    d = 0
    out = {}
    k = idx[head]
    while k < len(stream) and stream[k][0] < until_va:
        a, sz, bs, mn, op, t = stream[k]
        out[a] = d
        out[a + sz] = d
        if mn == "push":
            d += 4
        elif mn == "pop":
            d -= 4
        elif mn == "sub" and op.startswith("esp, "):
            try:
                d += int(op.split(", ")[1], 0)
            except Exception:
                pass
        elif mn == "add" and op.startswith("esp, "):
            try:
                d -= int(op.split(", ")[1], 0)
            except Exception:
                pass
        k += 1
    return out


def delta_at(head, va):
    m = delta_walk(head, va + 1)
    if va in m:
        return m[va]
    # nearest at or before va
    k = bisect.bisect_right(addrs, va) - 1
    while k >= 0 and stream[k][0] < head:
        k -= 1
    while k >= 0:
        for cand in (stream[k][0], stream[k][0] + stream[k][1]):
            if cand in m:
                return m[cand]
        k -= 1
    return 0


def phys_slot(head, va, src):
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", src)
    if not m:
        return None
    x = int(m.group(1), 16) if m.group(1).startswith("0x") else int(m.group(1))
    d = delta_at(head, va)
    return x - d


def head_of(c):
    lo = R62.frame_lo(c)
    # true head = first insn at/after lo that is an E8 target or lo itself;
    # simpler: head containing c per gate CHAIN host analysis not available;
    # use lo as frame base for delta (frame base == head-esp right after head's
    # sub/pushes? NO -- delta must start at head BEFORE sub esp (esp is caller's).
    # Convention: head = aligned caller target; find via E8T scan downward.
    E8T = set(callers)
    k = bisect.bisect_right(addrs, lo) - 1
    for j in range(k, max(0, k - 40), -1):
        if stream[j][0] in E8T:
            return stream[j][0]
    return lo


print("== F=0x778a20 physical slots")
H = 0x778a20
for va, desc in [(0x778ac7, "mov [esp+0x38],edi"), (0x778ae5, "VT store [esp+0x34]"),
                 (0x778bcb, "witness lea [esp+0x38]"), (0x778dcd, "witness lea [esp+0x38]"),
                 (0x778e20, "witness lea [esp+0x38]"), (0x778acf, "[esp+0x34]=7e1b0c"),
                 (0x778ae0, "lea ecx,[esp+0x34]")]:
    src = desc[desc.index("["):]
    print("  %08x %-24s delta=%d phys_slot=0x%x" % (va, desc, delta_walk(H, va)[va], phys_slot(H, va, src) or -1))

print("== edi provenance at 0x778ac7 (nearest mov edi,... in [H,ac7))")
w = R62.nearest_writer("edi", 0x778ac7, True, H)
print("  ", w and (hex(w[0]), w[1], w[2], w[3]))
# walk further if via reg
if w and w[3] in G61.__dict__.get("REGS", ()):
    w2 = R62.nearest_writer(w[3], w[0], True, H)
    print("   ->", w2 and (hex(w2[0]), w2[1], w2[2], w2[3]))

print("\n== per bare row: head, witness lea phys slot, matching VT store in head window")
for c in BARE:
    lo = R62.frame_lo(c)
    h = head_of(c)
    k = idx[c] - 1
    _, _, _, mn, op, _t = stream[k]
    ps = phys_slot(h, stream[k][0], op)
    hits = []
    for s in VT_SITES:
        if h <= s < h + 0x1000 and R62._ctx["TLO"] <= s < G61._ctx["THI"]:
            sh = head_of(s)
            if sh != h:
                continue
            a, sz, bs, mn2, op2, t2 = stream[idx[s]]
            p = phys_slot(h, s, op2)
            hits.append((hex(s), op2, p, "MATCH" if p == ps else "no"))
    print("  row %06x head=%08x lea %s phys=0x%x VTstores=%s" % (c, h, op, ps or 0, hits))

print("\n== host 0x528C00 body: mov [ecx],imm32 / call ctor census")
k = idx[0x528c00]
cnt = 0
for j in range(k, min(k + 200, len(stream))):
    a, sz, bs, mn, op, t = stream[j]
    if mn == "mov" and op.startswith("dword ptr [ecx], 0x"):
        print("  %08x %s %s" % (a, bs, op))
        cnt += 1
    if cnt > 6:
        break
print("  first 8 insns:")
showk = idx[0x528c00]
for j in range(showk, showk + 8):
    a, sz, bs, mn, op, t = stream[j]
    print("   %08x %-14s %s %s" % (a, bs, mn, op))
