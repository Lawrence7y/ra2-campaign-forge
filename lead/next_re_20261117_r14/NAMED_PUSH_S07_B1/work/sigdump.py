# -*- coding: utf-8 -*-
"""Compact per-site signature from analysis.json (calls/rets/path action signatures)."""
import os, sys, json
WORK = os.path.dirname(os.path.abspath(__file__))
ana = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
sel = sys.argv[1:] if len(sys.argv) > 1 else list(ana.keys())
def sigstr(sig):
    return "calls=%s rets=%s ret=%s end_eax=%s" % (
        [("%08X"%x) for x in sig.get("calls",[])],
        [("%08X"%x) for x in sig.get("rets",[])],
        sig.get("has_ret"), sig.get("end_eax"))
for e in sel:
    r = ana[e]
    print("=" * 80)
    print("%s %s  chA p1/p2/p3=%d/%d/%d chB=%d" % (
        e, r["hint_name"], r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chB"])))
    for s in r["chA_sites"]:
        callee = ("%08X"%int(s["callee"])) if s.get("callee") else "INDIRECT"
        prof = s.get("callee_profile",{})
        print("  call@%s callee=%s %s imm=%s jcc=%s->%s" % (
            s["call_addr"], callee, s["test_kind"], s["test_imm"], s["jcc_mnemonic"], s.get("jcc_target")))
        print("    TAKEN:   %s" % sigstr(s.get("sig_taken",{})))
        print("    FALLTHR: %s" % sigstr(s.get("sig_fallthrough",{})))
        print("    prof: falsy=%s consts=%s nrets=%s origins=%s" % (
            s.get("p3_form"), prof.get("all_consts"), prof.get("n_rets"), prof.get("origins")))
