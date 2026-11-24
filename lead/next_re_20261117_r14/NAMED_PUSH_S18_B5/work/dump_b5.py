# -*- coding: utf-8 -*-
"""Compact per-row dump of channel-A sites + eax traps + witness data for B5 manual verdict."""
import os, sys, json
WORK = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))
for r in rows:
    print("="*100)
    print("ENTRY %s  %s  atlas_size=%s n_insn=%d in_text=%s body_end=%08X(%s) skipdata=%d" % (
        r["entry"], r["hint_name"], r["atlas"].get("size"), r["n_insn_disasm"],
        r["in_text"], r["body_end"], r["body_end_in_text"], r["n_skipdata"]))
    print("-- first insns --")
    for x in r["first_insns"][:10]: print("   ", x)
    print("-- chA p1=%d p2=%d p3=%d  sites=%d --" % (r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chA_sites"])))
    trapmap = {t["call_addr"]: t for t in r["chA_eax_trap"]}
    for s in r["chA_sites"]:
        cp = s["callee_profile"]
        print("   call@%s callee=%s form=%s test=%s imm=%s jcc=%s->%s" % (
            s["call_addr"], cp.get("callee_key"), s["p3_form"], s["test_kind"],
            s["test_imm"], s["jcc_mnemonic"], ("%08X"%s["jcc_target"]) if isinstance(s["jcc_target"],int) else s["jcc_target"]))
        print("        falsy=%s consts=%s n_rets=%s origins=%s" % (
            s.get("call_site_falsy"), cp.get("all_consts"), cp.get("n_rets"), cp.get("origins")))
        print("        sig_t=%s sig_f=%s" % (s["sig_taken"], s["sig_fallthrough"]))
        t = trapmap.get(s["call_addr"],{})
        print("        EAX_TRAP(overwritten=%s)" % t.get("eax_overwritten"))
    print("-- direct callers (%d): %s --" % (len(r["direct_callers"]), r["direct_callers"]))
    for s in r["slots"]:
        print("-- slot %s rtti=%s vt=%s off=%s col=%s td=%s --" % (
            s.get("slot_va"), s.get("rtti_name"), s.get("vtable_base"), s.get("slot_off"),
            s.get("col"), s.get("td")))
        gws = s.get("global_writes",[])
        print("     global_writes=%d imm_loads=%s" % (len(gws), s.get("imm_loads")))
        for g in gws:
            inf = g.get("in_func")
            print("       write=%s global=%s in_func=%s atexit=%s" % (
                g.get("write_va"), g.get("global"),
                ("%08X"%inf[0]) if inf else None, g.get("atexit")))
        print("     dispatch_sites=%d sample=%s" % (len(s.get("dispatch_sites",[])), s.get("dispatch_sites",[])[:8]))
