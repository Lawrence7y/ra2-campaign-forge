# -*- coding: utf-8 -*-
"""从 analysis.json 出紧凑摘要，便于逐行裁定。"""
import os, json
WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
for rec in A:
    print("=" * 100)
    print("[%2d] %s  %s  (atlas_size=%s insn=%s skip=%s ret=%s last=%s)" % (
        rec["idx"], rec["entry"], rec["name"], rec["ring1"].get("atlas_size"),
        rec["ring1"].get("n_disasm"), rec["ring1"].get("n_skipdata"),
        rec["ring1"].get("ends_with_ret_or_jmp"), rec["ring1"].get("last")))
    chA = rec.get("chA", {})
    print("  3A sites p1/p2/p3=%s/%s/%s:" % (chA.get("p1"), chA.get("p2"), chA.get("p3")))
    for s in chA.get("sites", []):
        print("    call@%s callee=%s test=%s imm=%s jcc=%s(%s) tgt=%s fall=%s form=%s falsy=%s prof=%s nrets=%s" % (
            "%08X" % s["call_addr"], ("%08X" % s["callee"]) if s["callee"] else None,
            s["test_kind"], s["test_imm"], "%08X" % s["jcc_addr"], s["jcc_mnemonic"],
            ("%08X" % s["jcc_target"]) if s["jcc_target"] else None,
            "%08X" % s["fallthrough"], s["p3_form"], s["call_site_falsy"],
            s["callee_profile"].get("all_consts"), s["callee_profile"].get("n_rets")))
    print("  3B tables:", rec.get("chB"))
    print("  ring2 slots (%d):" % len(rec.get("ring2_slots", [])))
    for sl in rec.get("ring2_slots", []):
        rn = sl.get("rtti_name")
        if rn:
            print("    slot=%s vbase=%s off=%s col=%s td=%s name=%s" % (
                sl["slot_va"], sl.get("vtable_base"), sl.get("slot_off"), sl.get("col"), sl.get("td"), rn))
            gw = sl.get("global_writes", [])
            print("       global_writes=%d imm_loads=%s" % (len(gw), sl.get("imm_loads")))
            for g in gw[:6]:
                inf = g.get("in_func")
                print("         w=%s global=%s in_func=%s atexit=%s" % (
                    g.get("write_va"), g.get("global"), inf, g.get("atexit")))
        else:
            print("    slot=%s sec=%s rtti=None" % (sl["slot_va"], sl.get("section")))
    print("  ring4 direct (%d): %s" % (len(rec.get("ring4_direct", [])), rec.get("ring4_direct")))
