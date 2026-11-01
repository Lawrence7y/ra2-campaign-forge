# -*- coding: utf-8 -*-
"""R-063b probe1: unknown-reg 12 rows, cross-frame second hop (read-only).

Reuses r062 gate machinery (import only). For each unknown-reg caller row:
 - find containing function head via breach(c) & E8-heads
 - census ALL writes of the dead-end register inside the function (mov/lea/
   pop/xor/add/...), plus push/pop restore sequence of the prologue/epilogue
 - if truly no writer: for every aligned caller of that head, backward-walk
   the dead-end reg at the call site -> hop-2 verdict
 - hop-2 rows that dead-end again at a callee-saved reg: hop-3.
Prints JSON-ish report; writes nothing to repo except this scratch file.
"""
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G

R62.load()
stream = R62._ctx["stream"]
idx = R62._ctx["idx"]
callers = R62._ctx["callers"]
pred = R62._ctx["pred"]
TLO, THI = R62._ctx["TLO"], G._ctx["THI"]
E8T = set(callers)

ROWS = [0x4f2ced, 0x4f2d5c, 0x4f2e30, 0x4f3219, 0x4f32a4, 0x4f32e9,
        0x4f332e, 0x4f337c, 0x4f33ca, 0x4f38f9, 0x4f39c1, 0x4f3bf3]

SAVED = ("ebx", "edi", "esi", "ebp")
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")


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


def deadend_reg(c):
    """reproduce gate chain and return (chain list, dead-end reg, last writer va)."""
    v, ch = R62.classify_call(c)
    assert v == "unknown-reg", (hex(c), v)
    # walk again manually to find the dead-end register
    lo = R62.frame_lo(c)
    w = R62.nearest_writer("ecx", c, False, lo)
    a, bs, mn, src = w
    if src not in REGS:
        raise AssertionError(hex(c))
    # src is the reg we then trace
    w2 = R62.nearest_writer(src, a, True, lo)
    if w2 is None:
        return ch, src, a
    a2, bs2, mn2, src2 = w2
    if src2 in REGS and src2 != "ecx" and R62.nearest_writer(src2, a2, True, lo) is None:
        return ch, src2, a2
    raise AssertionError("unexpected deeper chain " + hex(c))


def reg_writers_all(reg, lo, hi_va):
    """every insn in stream index range [idx[lo], hi_va) that writes reg."""
    out = []
    end = idx[lo]
    while end < len(stream) and stream[end][0] < hi_va:
        end += 1
    for k in range(idx[lo], end):
        a, sz, bs, mn, op, tgt = stream[k]
        if mn in ("mov", "lea", "pop", "xor", "add", "sub", "and", "or", "sbb",
                  "cdq", "cmc") and re.match(r"^(?:dword ptr )?\b%s\b[,\]]?" % reg, op) \
                or mn == "pop" and op == reg:
            out.append((a, mn, op, bs))
        elif mn.startswith("cmov") and op.startswith(reg + ","):
            out.append((a, mn, op, bs))
        elif mn in ("xchg",) and re.match(r"^%s," % reg, op):
            out.append((a, mn, op, bs))
    return out


def frame_span(head):
    """head -> its frame window: from head to first ret reached in linear order
    that terminates (conservative: use [head, next-head) is unsafe; just use
    ret-bounded like gate but forward). For writer census use whole
    [head, head+scan) until a ret AND also next aligned head beyond."""
    return head


def hop_at(call_site, reg):
    """classify value of `reg` at a call site (backward walk in caller frame)."""
    lo = R62.frame_lo(call_site)
    w = R62.nearest_writer(reg, call_site, True, lo)
    if w is None:
        return ("dead-in", None, lo)
    a, bs, mn, src = w
    m = re.match(r"^0x([0-9a-f]+)$", src)
    if m:
        v = int(m.group(1), 16)
        return ("global-load" if v in G.GLOBALS else "imm32:%08X" % v, (a, bs), lo)
    slot = R62.esp_slot(src)
    if slot:
        if mn == "lea":
            return ("stack-object(lea esp+%s)" % slot, (a, bs), lo)
        wr = R62.slot_writers(slot, call_site)
        return ("param-slot[%s]" % slot if not wr else "local-slot[%s]" % slot,
                (a, bs), lo)
    if src == reg:
        return ("self-copy?", (a, bs), lo)
    if src in REGS:
        return ("via-reg:%s" % src, (a, bs), lo)
    return ("other", (a, bs, mn, src), lo)


def out():
    report = {}
    for c in ROWS:
        ch, reg, last_wa = deadend_reg(c)
        rs = breach(c) & E8T
        heads = sorted(rs)
        lo = R62.frame_lo(c)
        rec = dict(row="%06x" % c, chain=ch, deadend=reg,
                   last_writer="%06x" % last_wa, frame_lo="%06x" % lo,
                   heads=[hex(h) for h in heads])
        # in-frame writes of dead-end reg between frame_lo and last writer insn
        wr = reg_writers_all(reg, lo, last_wa + 1)
        rec["inframe_writers_%06x_to_row" % lo] = [(hex(a), mn, op, bs) for a, mn, op, bs in wr]
        if len(heads) == 1:
            head = heads[0]
            # prologue bytes + push/pop census over [head, head+0x60)
            k = idx[head]
            prolog = [(hex(stream[i][0]), stream[i][3], stream[i][4])
                      for i in range(k, min(k + 24, len(stream)))]
            rec["head_prologue"] = prolog[:12]
            cl = sorted(callers.get(head, []))
            rec["F_callers"] = [hex(x) for x in cl]
            hop2 = {}
            for g_site in cl:
                v, ev, glo = hop_at(g_site, reg)
                hop2["%06x" % g_site] = (v, ev and (hex(ev[0]), ev[1]))
                if v.startswith("via-reg:"):
                    r2 = v.split(":")[1]
                    w2 = R62.nearest_writer(r2, g_site, True, glo)
                    if w2 is None:
                        hop2["%06x" % g_site] = (v + "->dead-in-%s" % r2, None)
                    else:
                        hop2["%06x" % g_site] = (v, (hex(w2[0]), w2[1], w2[2], w2[3]))
            rec["hop2"] = hop2
        report["%06x" % c] = rec
    print(json.dumps(report, indent=1))


out()
