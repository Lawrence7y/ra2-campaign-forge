# -*- coding: utf-8 -*-
"""Compact dump of analysis.json key facts for manual four-ring review."""
import os, json
WORK = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(WORK,"analysis.json"), encoding="utf-8"))
for r in data:
    print("="*100)
    print("%s  %-30s in_text=%s ndis=%d nskip=%d size=%d" % (
        r["entry"], r["hint_name"], r["in_text"], r["n_insn_disasm"], r["n_skipdata"], r["atlas"].get("size",0)))
    print("  direct_callers(%d): %s" % (len(r["direct_callers"]), ", ".join(r["direct_callers"][:8])))
    for s in r["slots"]:
        print("  SLOT va=%s sec=%s vt=%s off=%s col=%s td=%s rtti=%s" % (
            s.get("slot_va"),s.get("section"),s.get("vtable_base"),s.get("slot_off"),
            s.get("col"),s.get("td"),s.get("rtti_name")))
        gw=[g.get("write_va") for g in s.get("global_writes",[]) if g.get("write_va")]
        if gw: print("    writes: %s" % ", ".join(gw[:10]))
        ds=s.get("dispatch_sites",[])
        if ds: print("    dispatch_sites(%d): %s" % (len(ds), ", ".join(ds[:8])))
    print("  chA p1=%d p2=%d p3=%d sites=%d" % (r["chA"]["p1"],r["chA"]["p2"],r["chA"]["p3"],len(r["chA_sites"])))
    for i,s in enumerate(r["chA_sites"][:8]):
        print("    A%d call=%s callee=%s %s imm=%s jcc=%s->%s" % (
            i,s["call_addr"], s.get("callee"), s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], s.get("jcc_target")))
        cp=s.get("callee_profile",{})
        if cp: print("       callee consts=%s nret=%s origins=%s" % (cp.get("all_consts"),cp.get("n_rets"),cp.get("origins")))
    traps=[x for x in r["chA_eax_trap"] if x["eax_overwritten"]]
    print("  eax_traps=%d" % len(traps))
    for t in traps[:3]: print("    trap: %s" % t["eax_overwritten"])
    if r["chB"]:
        for b in r["chB"]:
            print("  chB jmp=%s %s table=%s bound=%s ncase=%d targets=%d" % (
                b["jmp_addr"],b["op_str"],b["table_va"],b["bound"],b["ncase"] or 0,len(b["targets"])))
