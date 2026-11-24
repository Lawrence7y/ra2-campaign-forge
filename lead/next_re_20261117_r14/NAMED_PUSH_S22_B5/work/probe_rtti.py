# -*- coding: utf-8 -*-
"""Probe raw .rdata around each vector slot_va; manually locate vtable base + RTTI COL/TD/name."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "dump.json"), encoding="utf-8") as f:
    dump = json.load(f)

def dump_word_range(va, n_before, n_after, label=""):
    print("--- %s around %08X ---" % (label, va))
    for a in range(va - n_before, va + n_after, 4):
        w = C.u32(a)
        tag = ""
        if w is not None:
            # try interpret as VA into a section; show ascii if plausible cstr
            sec = C.va_in(w)
            if sec:
                tag += " ->%s" % sec
            # try reading a cstr at this VA (in case it's a name ptr)
        print("  %08X : %08X%s" % (a, w if w is not None else 0, tag))

for entry, d in dump.items():
    print("=" * 100)
    print(entry, d["name"])
    for s in d["slots"]:
        sv = int(s["slot_va"], 16)
        print("  slot_va =", s["slot_va"])
        # dump +/- 0x40 around slot
        dump_word_range(sv, 0x40, 0x40, "slot")
        # scan backwards up to 0x200 for a COL(sig=0) with TD name .?AV (wider than resolve_slot's 40 words)
        found = []
        for k in range(0, 0x80):
            vb = sv - 4 * k
            col = C.u32(vb - 4)
            if not col or not C.va_in(col):
                continue
            sig = C.u32(col)
            if sig != 0:
                continue
            td = C.u32(col + 0xC)
            if not td or not C.va_in(td):
                continue
            name = C.read_cstr(td + 8, 200)
            if ".?AV" in name:
                found.append((vb, k, col, td, name))
        print("  WIDE COL scan found:", len(found))
        for vb, k, col, td, name in found[:6]:
            print("     vb=%08X slot_no=%d col=%08X td=%08X name=%s" % (vb, k, col, td, name))
