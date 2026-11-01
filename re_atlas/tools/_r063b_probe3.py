# -*- coding: utf-8 -*-
"""R-063b probe3: (a) unknown-reg full multi-hop chain verify; (b) bare rows
construction census: F-frame indirect/relay forms + data-segment VT holders."""
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
TLO, THI = R62._ctx["TLO"], G61._ctx["THI"]
VT = 0x7E1B04

ROWS = [0x4f2ced, 0x4f2d5c, 0x4f2e30, 0x4f3219, 0x4f32a4, 0x4f32e9,
        0x4f332e, 0x4f337c, 0x4f33ca, 0x4f38f9, 0x4f39c1, 0x4f3bf3]


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


def show(a, b):
    k = bisect.bisect_left(addrs, a)
    while k < len(stream) and stream[k][0] < b:
        va, sz, bs, mn, op, t = stream[k]
        print("  %08x: %-14s %-6s %s%s" % (va, bs, mn, op,
              " ->%x" % t if t and mn in ("call", "jmp") else ""))
        k += 1


def jmp_refs(target):
    """jmp/jcc sites in .text whose resolved target == target."""
    out = []
    for a, sz, bs, mn, op, t in stream:
        if t == target and mn in ("jmp",) or (mn.startswith("j") and t == target):
            out.append((hex(a), mn, bs))
    return out


def data_refs(target):
    """raw dword occurrences of VA target in disk-backed non-.text sections."""
    blob = R62._ctx["BLOB"]
    imm = struct.pack("<I", target)
    IB = R62._ctx["IB"]
    hits = []
    pos = 0
    while True:
        i = blob.find(imm, pos)
        if i < 0:
            break
        pos = i + 1
        for s, vs, rp, rs in R62._ctx["SECS"]:
            if rp <= i < rp + rs:
                va = IB + s + (i - rp)
                if not (TLO <= va < THI):
                    hits.append(hex(va))
    return hits


def reg_src_at(reg, call_va):
    lo = R62.frame_lo(call_va)
    w = R62.nearest_writer(reg, call_va, True, lo)
    return lo, w


# ---------- (a) full hop chain ----------
print("== (a) MULTI-HOP for 12 unknown-reg rows")
HUB = 0x4f38b0
for c in ROWS:
    v, ch = R62.classify_call(c)
    lo = R62.frame_lo(c)
    # hop2: containing head + prologue esi/edx writers
    heads = sorted(breach(c) & E8T)
    F = heads[0]
    # writer of deadend reg in WHOLE F function (head .. next aligned head after F?)
    print("row %06x chain=%s heads=%s F=%08x" % (c, ch, [hex(x) for x in heads], F))
    k = idx[F]
    prov = []
    q = k
    while q < len(stream) and stream[q][0] < c:
        a, sz, bs, mn, op, t = stream[q]
        if mn == "mov" and (op == "esi, edx" or op == "edx, esi" or op.startswith("edi, ecx")):
            prov.append((hex(a), bs, mn, op))
        q += 1
    print("   F-entry reg-moves: %s" % prov[:4])
    if F == HUB:
        cls = "edx"
    else:
        cls = "edx"
    # hop3: callers of F
    cl = sorted(callers.get(F, []))
    for g in cl:
        lo3, w3 = reg_src_at(cls, g)
        print("   caller@%08x frame_lo=%08x edx<-w=%s" % (g, lo3, w3))
        if w3 and w3[3] in ("esi",):
            lo4, w4 = reg_src_at("esi", w3[0])
            print("      esi<-w=%s" % str(w4))
print("\n== inbound refs (jmp / data) for hubs")
for t in (0x4f2c70, 0x4f3140, 0x4f3b80, HUB):
    print("target %08x: jmp_refs=%s data_refs=%s aligned_callers=%s" % (
        t, jmp_refs(t), data_refs(t), [hex(x) for x in sorted(callers.get(t, []))]))

# ---------- (b) bare rows construction census ----------
print("\n== (b) BARE ROWS: F-frame all writes near the slot + VT census")
VTB = b"\x04\x1b\x7e\x00"
blob = R62._ctx["BLOB"]
IB = R62._ctx["IB"]
# data-section VA holders of the dword 0x7E1B04 (relay-load candidates)
holders = []
pos = 0
while True:
    i = blob.find(VTB, pos)
    if i < 0:
        break
    pos = i + 1
    for s, vs, rp, rs in R62._ctx["SECS"]:
        if rp <= i < rp + rs:
            va = IB + s + (i - rp)
            if not (TLO <= va < THI):
                holders.append(va)
print("data holders of 07E1B04 dword: %s" % [hex(h) for h in holders])


def frame_bounds(va):
    lo = R62.frame_lo(va)
    heads = sorted(breach(va) & E8T)
    return lo, heads


def slot_reg_flows(F, lo, hi, slot):
    """returns (direct_stores, lea_sites, indirect_stores) for [esp+slot] in F."""
    direct, leas, indirect = [], [], []
    k = idx[lo]
    while k < len(stream) and stream[k][0] < hi:
        a, sz, bs, mn, op, t = stream[k]
        if mn == "mov" and re.match(r"^dword ptr \[esp \+ %s\], " % re.escape(slot), op):
            direct.append((hex(a), bs, op))
        if mn == "lea":
            m = re.match(r"^(\w+), \[esp \+ %s\]$" % re.escape(slot), op)
            if m:
                leas.append((hex(a), bs, mn, op))
        k += 1
    # indirect stores: any `mov [reg(+disp)], src` where reg is one of the lea'd
    # regs, occurring AFTER a lea site
    learegs = {}
    k = idx[lo]
    while k < len(stream) and stream[k][0] < hi:
        a, sz, bs, mn, op, t = stream[k]
        if mn == "lea":
            m = re.match(r"^(\w+), \[esp \+ %s\]$" % re.escape(slot), op)
            if m:
                learegs[m.group(1)] = a
        if mn == "mov":
            m = re.match(r"^dword ptr \[(\w+)(?: \+ (0x[0-9a-f]+|\d+))?\], (.+)$", op)
            if m and m.group(1) in learegs and a > learegs[m.group(1)]:
                indirect.append((hex(a), bs, op, "base=%s" % m.group(1)))
        k += 1
    return direct, leas, indirect


BARE = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c, 0x5cf4c7,
        0x5d76a9, 0x76c555, 0x778bcf, 0x778dd1, 0x778e24]
for c in BARE:
    lo = R62.frame_lo(c)
    heads = sorted(breach(c) & E8T)
    F = heads[0]
    k = idx[c] - 1
    _, _, _, mn, op, _t = stream[k]
    slot = R62.esp_slot(op)
    # scan whole F function: from head until an epilogue ret after last witness call?
    # use window [F, F+0x1000) conservatively but stop at next aligned head > F
    nxt_heads = sorted(h for h in E8T if h > F)
    hi = nxt_heads[0] if nxt_heads else F + 0x400
    direct, leas, indirect = slot_reg_flows(F, lo, c, slot)
    # also VT imm stores anywhere in F frame
    vt_in_F = []
    q = idx[F]
    while q < len(stream) and stream[q][0] < min(hi, 0xFFF + F):
        a, sz, bs, mn, op, t = stream[q]
        if "041b7e00" in bs:
            vt_in_F.append((hex(a), mn, op, bs))
        q += 1
    print("row %06x F=%08x slot=%s direct=%d leas=%s indirect=%d vt_stores_in_F=%s" % (
        c, F, slot, len(direct), [(x[0], x[3]) for x in leas], len(indirect), vt_in_F))
