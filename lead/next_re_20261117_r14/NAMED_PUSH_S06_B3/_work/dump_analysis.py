# -*- coding: utf-8 -*-
"""Compact dump of analysis.json for manual per-row adjudication."""
import os, json
WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
for rec in A:
    print("=" * 100)
    print("#%d %s %s size=%s" % (rec["idx"], rec["entry"], rec["name"], rec.get("size")))
    ri = rec["ring1"]
    print("  R1: in_text=%s atlas=%s insn=%s skip=%s first=[%s] last=[%s] ends_ret_jmp=%s" % (
        ri.get("in_text"), ri.get("atlas_size"), ri.get("n_disasm"), ri.get("n_skipdata"),
        ri.get("first"), ri.get("last"), ri.get("ends_with_ret_or_jmp")))
    for s in rec["ring2_slots"]:
        if s.get("rtti_name"):
            print("  R2: slot_va=%s section=%s vt=%s off=%s(#%d) col=%s td=%s nameva=%s name=%s" % (
                s["slot_va"], s["section"], s["vtable_base"], s["slot_off"], s["slot_off"]//4,
                s["col"], s["td"], s["name_va"], s["rtti_name"]))
            gw = s.get("global_writes", [])
            print("      vptr_writes=%d" % len(gw))
            for g in gw[:8]:
                print("        write=%s global=%s in_func=%s atexit=%s" % (
                    g.get("write_va"), g.get("global"),
                    g.get("in_func"), g.get("atexit")))
            print("      imm_loads=%s" % s.get("imm_loads", [])[:6])
        else:
            print("  R2(raw): slot_va=%s section=%s (no RTTI)" % (s.get("slot_va"), s.get("section")))
    ca = rec.get("chA", {})
    print("  R3A: p1=%s p2=%s p3=%s" % (ca.get("p1"), ca.get("p2"), ca.get("p3")))
    for st in ca.get("sites", []):
        print("    site call=%s callee=%s test@%s(%s imm=%s) jcc=%s@%s tgt=%s fall=%s" % (
            st.get("call_addr"), st.get("callee"), st.get("test_addr"), st.get("test_kind"),
            st.get("test_imm"), st.get("jcc_mnemonic"), st.get("jcc_addr"),
            st.get("jcc_target"), st.get("fallthrough")))
        print("      form=%s call_site_falsy=%s" % (st.get("p3_form"), st.get("call_site_falsy")))
        print("      callee_prof=%s" % st.get("callee_profile"))
        print("      taken=%s" % st.get("sig_taken"))
        print("      fallthrough=%s" % st.get("sig_fallthrough"))
    cb = rec.get("chB", [])
    if cb:
        print("  R3B: %s" % cb)
