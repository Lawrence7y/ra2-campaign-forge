# -*- coding: utf-8 -*-
"""打印 analysis.json 的 ②/④ 证据摘要，便于逐行判读。"""
import json, os
WORK = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
for r in data:
    print("=" * 100)
    print("%s  %s  in_text=%s size=%s disasm_insn=%d skipdata=%d" % (
        r["entry"], r["hint_name"], r["in_text"], r["atlas"].get("size"),
        r["n_insn_disasm"], r["n_skipdata"]))
    print("  ③ chA p1/p2/p3 = %s ; chB tables=%d ; eax_trap sites=%d" % (
        r["chA"], len(r["chB"]), sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"])))
    print("  direct_callers(%d): %s" % (len(r["direct_callers"]), ",".join(r["direct_callers"][:12])))
    for s in r["slots"]:
        print("  SLOT slot_va=%s sec=%s vt_base=%s off=%s rtti=%r" % (
            s.get("slot_va"), s.get("section"), s.get("vtable_base"), s.get("slot_off"), s.get("rtti_name")))
        if s.get("rtti"):
            print("      (no RTTI resolved)")
        gw = s.get("global_writes", [])
        print("      global_writes=%d imm_loads=%d dispatch_sites=%d" % (
            len(gw), len(s.get("imm_loads", [])), len(s.get("dispatch_sites", []))))
        for g in gw[:12]:
            inf = g.get("in_func")
            infs = ("%s(size=%s)" % (inf[1], inf[2])) if inf else None
            print("        write=%s global=%s in_func=%s atexit=%s" % (
                g.get("write_va"), g.get("global"), infs, g.get("atexit")))
        if s.get("imm_loads"):
            print("        imm_loads=%s" % ",".join(s["imm_loads"][:12]))
        if s.get("dispatch_sites"):
            print("        dispatch_sites=%s" % ",".join(s["dispatch_sites"][:20]))
