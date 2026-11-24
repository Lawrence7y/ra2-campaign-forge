# -*- coding: utf-8 -*-
"""对 13 个 channel-A 命中逐个求环②（vtable/RTTI）与环④（direct/ctor/dispatch）见证。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import witness_core as W

WORK = os.path.dirname(os.path.abspath(__file__))
screen = json.load(open(os.path.join(WORK, "screen.json"), encoding="utf-8"))
a_hits = [r for r in screen if r["A_hit"]]

out = []
for r in a_hits:
    wit = W.witness_entry(r["entry"])
    out.append({
        "entry": r["entry"], "grade": r["grade"], "name": r["name"],
        "atlas_size": r["atlas_size"], "n_insn": r["n_insn"],
        "A_sites": r["A_sites"],
        "direct_callers": wit["direct_callers"],
        "slots": wit["slots"],
    })
    print("%s %-28s direct=%s slots=%d" % (
        r["entry"], r["name"][:28], wit["direct_callers"][:4], len(wit["slots"])))
    for s in wit["slots"][:4]:
        rtti = s.get("rtti_name")
        gws = s.get("global_writes", [])
        ctor = [g for g in gws if not g.get("atexit")]
        print("   slot@%s vbase=%s off=%s rtti=%s ctor_writes=%d atexit_writes=%d" % (
            s["slot_va"], s.get("vtable_base"), s.get("slot_off"), rtti,
            len(ctor), sum(1 for g in gws if g.get("atexit"))))

json.dump(out, open(os.path.join(WORK, "witness.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nwrote witness.json (%d entries)" % len(out))
