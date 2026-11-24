# -*- coding: utf-8 -*-
"""输出每行 hex 化的 ③b② 站点 + ②④ 摘要，作为逐行 EVIDENCE 落盘依据。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
def hx(x):
    return "None" if x is None or x == "None" else "%08X" % (int(x) & 0xFFFFFFFF)
for r in data:
    print("=" * 100)
    print("%s %s | in_text=%s size=%s skipdata=%d" % (
        r["entry"], r["hint_name"], r["in_text"], r["atlas"].get("size"), r["n_skipdata"]))
    print("  chA p1/p2/p3=%s chB=%d" % (r["chA"], len(r["chB"])))
    for i, s in enumerate(r["chA_sites"]):
        cp = s["callee_profile"]
        print("  site%d call=%s callee=%s %s imm=%s jcc=%s->%s form=%s" % (
            i, hx(s["call_addr"]), hx(s.get("callee")), s["test_kind"],
            s["test_imm"], s["jcc_mnemonic"], hx(s.get("jcc_target")), s["p3_form"]))
        print("     cconsts=%s nrets=%s origins=%s" % (
            cp.get("all_consts"), cp.get("n_rets"), cp.get("origins")))
        print("     T=%s" % s["sig_taken"])
        print("     F=%s" % s["sig_fallthrough"])
    if r["chB"]:
        for t in r["chB"]:
            print("  chB jmp=%s bound=%s ncase=%d targets=%s" % (
                t["jmp_addr"], t["bound"], t["ncase"],
                ",".join(x["target"] for x in t["targets"])))
    dc = r["direct_callers"]
    print("  direct(%d)=%s" % (len(dc), ",".join(dc[:8])))
    for s in r["slots"]:
        if s.get("rtti_name"):
            gw = [g.get("write_va") for g in s.get("global_writes", []) if g.get("write_va")]
            print("  SLOT vt=%s off=%d slot=%d name=%s" % (
                s.get("vtable_base"), int(s.get("slot_off")), int(s.get("slot_off"))//4, s.get("rtti_name")))
            print("     install=%s dispatch=%d" % (",".join(gw[:8]), len(s.get("dispatch_sites", []))))
        else:
            print("  SLOT(no-rtti) va=%s" % s.get("slot_va"))
