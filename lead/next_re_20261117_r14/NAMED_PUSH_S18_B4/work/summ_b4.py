# -*- coding: utf-8 -*-
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))
for r in rows:
    print("="*120)
    print("%s %s  size=%s ninsn=%d skip=%d in_text=%s body_end=%08X end_in_text=%s" % (
        r["entry"], r["hint_name"], r["atlas"].get("size"), r["n_insn_disasm"], r["n_skipdata"],
        r["in_text"], r["body_end"], r["body_end_in_text"]))
    print("  ① first:", " | ".join(r["first_insns"][:4]))
    print("  ① last :", " | ".join(r["last_insns"][-4:]))
    print("  --- slots (②) ---")
    for s in r["slots"]:
        if s.get("rtti_name"):
            gw = s.get("global_writes", [])
            atx = [g for g in gw if g.get("atexit")]
            print("    slot_va=%s vt=%s off=%s COL=%s TD=%s name=%s" % (
                s["slot_va"], s["vtable_base"], s["slot_off"], s["col"], s["td"], s["rtti_name"]))
            print("       dispatch_sites=%d global_writes=%d atexit_writes=%d imm_loads=%d" % (
                len(s.get("dispatch_sites",[])), len(gw), len(atx), len(s.get("imm_loads",[]))))
            for g in gw[:6]:
                inf = g.get("in_func")
                print("         gw write=%s glob=%s in_func=%s atexit=%s" % (
                    g.get("write_va"), g.get("global"),
                    ("%08X"%inf[0]) if inf else None, g.get("atexit")))
        else:
            print("    slot_va=%s rtti=None" % s["slot_va"])
    print("  --- chA (③b②) p1=%d p2=%d p3=%d sites=%d ---" % (
        r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chA_sites"])))
    for s in r["chA_sites"]:
        print("    call=%s callee=%s test=%s kind=%s imm=%s jcc=%s->%s form=%s falsy=%s" % (
            s["call_addr"], s.get("callee"), s["test_addr"], s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], s.get("jcc_target"), s["p3_form"], s.get("call_site_falsy")))
        print("       prof=%s" % s["callee_profile"])
        print("       T=%s" % s["sig_taken"])
        print("       F=%s" % s["sig_fallthrough"])
    print("  eax_trap:", r["chA_eax_trap"])
    print("  --- chB (③b①) count=%d ---" % len(r["chB"]))
    for t in r["chB"]:
        print("    jmp=%s table=%s bound=%s ncase=%s targets=%d" % (
            t["jmp_addr"], t["table_va"], t["bound"], t["ncase"], len(t["targets"])))
    print("  ④ direct_callers=%d %s" % (len(r["direct_callers"]), r["direct_callers"][:8]))
