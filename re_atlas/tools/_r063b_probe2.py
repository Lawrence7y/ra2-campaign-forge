# -*- coding: utf-8 -*-
"""R-063b probe2: GenericList bare-stack rows -- outer-frame vptr construction.

Read-only. Reuses R-062 gate (import only).
1) re-derive 17 stack-object rows, split constructed(5)/bare(12) by in-frame
   slot dword writes (same recipe as _crev_engine E9).
2) image-wide census of every encoding writing imm32 0x7E1B04 (c7 forms,
   push imm, mov reg,imm, cmp ...) -> candidate vptr-stamp sites.
3) for each bare row: find containing head F=breach(row)&E8T, its aligned
   callers G_i; in G_i frame scan ANY write of a slot that (a) holds
   0x7E1B04 stamp form or (b) is the lea'd slot; also flag if the frame passes
   [esp+X] downward.
"""
import re
import sys
import os
import json
import struct
import bisect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G61

R62.load()
stream = R62._ctx["stream"]
idx = R62._ctx["idx"]
callers = R62._ctx["callers"]
pred = R62._ctx["pred"]
addrs = [s[0] for s in stream]
VT = 0x7E1B04

BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]


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

# ---- 1) verify split
so = []
for host in G61.SMALL:
    for c in sorted(callers.get(host, [])):
        if R62.classify_call(c)[0] == "stack-object":
            so.append(c)
constructed = []
bare = []
for c in so:
    lo = R62.frame_lo(c)
    # slot from the lea right before call
    k = idx[c] - 1
    _, _, _, mn, op, _t = stream[k]
    slot = R62.esp_slot(op)
    wr = R62.slot_writers(slot, c)
    vp = [x for x in wr if "041b7e00" in x[1]]
    (constructed if vp else bare).append((c, slot, [hex(x[0]) for x in vp], len(wr)))
assert len(bare) == 12 and set(x[0] for x in bare) == set(BARE), (bare, constructed)
print("SPLIT OK. constructed=%s" % [(hex(c), s, v) for c, s, v, n in constructed])
print("bare=%s" % [(hex(c), s, nwr) for c, s, v, nwr in bare])

# ---- 2) image-wide imm32 0x7E1B04 occurrences (aligned-insn scan + raw scan)
imm = struct.pack("<I", VT)
blob = R62._ctx["BLOB"]
raw_hits = []
pos = 0
while True:
    i = blob.find(imm, pos)
    if i < 0:
        break
    raw_hits.append(i)
    pos = i + 1
# file-offset -> VA
secs = R62._ctx["SECS"]
IB = R62._ctx["IB"]


def off_to_va(off):
    for s, vs, rp, rs in secs:
        if rp <= off < rp + rs:
            return IB + s + (off - rp)
    return None


ins_at = {}
for a, sz, bs, mn, op, t in stream:
    ins_at[a] = (bs, mn, op)


def insn_containing(va):
    j = bisect.bisect_right(addrs, va) - 1
    if j < 0:
        return None
    a, sz, bs, mn, op, t = stream[j]
    if a <= va < a + sz:
        return (a, mn, op, bs)
    return None


print("\nIMG-WIDE imm32 %08X occurrences:" % VT)
forms = {}
for off in raw_hits:
    va = off_to_va(off)
    if va is None:
        print("  off %08X (not disk-backed/BSS)" % off)
        continue
    in_text = R62._ctx["TLO"] <= va < G61._ctx["THI"]
    cont = insn_containing(va) if in_text else None
    print("  VA %08X %s %s" % (va, "text" if in_text else "data",
                               ("insn=%s %s [%s]" % (cont[1], cont[2], cont[0] and hex(cont[0]))) if cont else ""))
    key = (cont[1], cont[2]) if cont else ("data", hex(va))
    forms.setdefault(key, 0)
    forms[key] += 1
print("forms:", json.dumps({("%s %s" % k): v for k, v in forms.items()}, indent=1))

# ---- 3) per bare row: containing head, callers, outer-frame vptr census
out = {}
for c, slot, _v, nwr in bare:
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    rec = dict(row="%06x" % c, slot=slot, frame_lo="%08x" % lo,
               heads=[hex(h) for h in heads],
               n_writers_in_frame=nwr)
    if len(heads) == 1:
        F = heads[0]
        cl = sorted(callers.get(F, []))
        rec["F_callers"] = [hex(x) for x in cl]
        outer = {}
        for g in cl:
            glo = R62.frame_lo(g)
            # every write of any [esp+X] in the outer frame whose imm or reg
            # provenance could be the vptr; look for: slot stores with imm32
            # VT, lea of a slot before the F-call (the object handle passed?)
            k = idx[g]
            span = []
            q = idx[glo]
            while q < k and stream[q][0] < g:
                a, sz, bs, mn, op, t = stream[q]
                if ("041b7e00" in bs) or (mn == "mov" and re.match(r"^dword ptr \[esp \+ 0x[0-9a-f]+\], 0x7e1b04$", op)):
                    span.append((hex(a), mn, op, bs))
                # also param-store / lea-to-call patterns around this call
                q += 1
            outer["%06x" % g] = dict(frame_lo="%08x" % glo, vptr_stores=span)
        rec["outer"] = outer
    out["%06x" % c] = rec
print("\nPER-BARE-ROW:")
print(json.dumps(out, indent=1))
