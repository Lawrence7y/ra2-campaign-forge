# -*- coding: utf-8 -*-
"""Summarize analysis.json into a compact per-row fact sheet (stdout, utf-8 safe)."""
import os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
AN = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
sys.path.insert(0, WORK)
import recore as R

for rec in AN:
    e = rec["entry"]
    r1 = rec["ring1"]
    print("=" * 110)
    print("ROW %s %s" % (e, rec["name"]))
    print("  ①: in_text=%s atlas=%s n=%s skip=%s first=%s | last=%s" % (
        r1.get("in_text"), r1.get("atlas_size"), r1.get("n_disasm"), r1.get("n_skipdata"),
        r1.get("first"), r1.get("last")))
    # ring2
    slots = rec.get("ring2_slots", [])
    rtti_slots = [s for s in slots if s.get("rtti_name")]
    print("  ②: total_refs=%d rtti_slots=%d" % (len(slots), len(rtti_slots)))
    for s in slots:
        if s.get("rtti_name"):
            sv = R.u32(int(s["slot_va"], 16))
            print("     slot=%s vt=%s off=+%s(#%s) col=%s td=%s name=%s slotval=%s%s" % (
                s["slot_va"], s["vtable_base"], s["slot_off"], s["slot_off"]//4,
                s["col"], s["td"], s["rtti_name"], "%08X" % sv if sv is not None else "?",
                " ==ENTRY" if sv == int(e,16) else " !=ENTRY"))
        else:
            print("     [no-rtti ref] slot=%s sec=%s" % (s.get("slot_va"), s.get("section")))
    # ring4
    direct = rec.get("ring4_direct", [])
    print("  ④: direct_callers=%d %s" % (len(direct), direct[:12]))
    for s in rtti_slots:
        gw = s.get("global_writes", [])
        live = [g for g in gw if not g.get("atexit")]
        print("     vt=%s global_writes=%d live(non-atexit)=%d imm_loads=%d" % (
            s["vtable_base"], len(gw), len(live), len(s.get("imm_loads", []))))
        for g in gw[:8]:
            inf = g.get("in_func")
            infs = ("%08X" % inf[0]) if inf else "?"
            print("       write=%s in_func=%s atexit=%s" % (
                g.get("write_va"), infs, g.get("atexit")))
    # ring3
    chA = rec.get("chA") or {}
    print("  ③A: p1=%s p2=%s p3=%s sites=%d" % (chA.get("p1"), chA.get("p2"), chA.get("p3"), len(chA.get("sites", []))))
    for st in chA.get("sites", []):
        cal = ("%08X" % st["callee"]) if st.get("callee") else "?"
        print("     site call=%08X callee=%s test=%s imm=%s jcc=%s->%s form=%s falsy=%s" % (
            st["call_addr"], cal, st.get("test_kind"), st.get("test_imm"),
            st.get("jcc_mnemonic"), ("%08X" % st["jcc_target"]) if st.get("jcc_target") else "?",
            st.get("p3_form"), st.get("call_site_falsy")))
        prof = st.get("callee_profile") or {}
        print("        prof consts=%s n_rets=%s origins=%s" % (
            prof.get("all_consts"), prof.get("n_rets"), prof.get("origins")))
        print("        sig_t=%s" % st.get("sig_taken"))
        print("        sig_f=%s" % st.get("sig_fallthrough"))
