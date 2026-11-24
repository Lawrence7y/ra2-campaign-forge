# -*- coding: utf-8 -*-
"""紧凑打印每行的 ③b② 站点签名，供筛选 pure-forwarding / bool / eax-trap。"""
import os, json
WORK = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
def va(x): return int(x,16) if isinstance(x,str) else int(x)
for r in data:
    print("="*100)
    print("%s %-28s size=%s p1/p2/p3=%s eaxtrap=%d" % (
        r["entry"], r["hint_name"], r["atlas"].get("size"), r["chA"],
        sum(1 for x in r["chA_eax_trap"] if x["eax_overwritten"])))
    for i,s in enumerate(r["chA_sites"]):
        st=s["sig_taken"]; sf=s["sig_fallthrough"]
        # 判断 pure-forwarding：两路都 has_ret=True，calls 都空，rets 仅差 eax 常量
        pf = (st["has_ret"] and sf["has_ret"] and not st["calls"] and not sf["calls"])
        print("  site%d call=%s callee=%s %s imm=%s jcc=%s->%08X" % (
            i, s["call_addr"], s.get("callee"), s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], va(s["jcc_target"]) if s.get("jcc_target") else 0))
        print("     p3form=%s falsy=%s callee_consts=%s n_rets=%s origins=%s" % (
            s["p3_form"], s.get("call_site_falsy"),
            s["callee_profile"].get("all_consts"), s["callee_profile"].get("n_rets"),
            s["callee_profile"].get("origins")))
        print("     T=%s" % st)
        print("     F=%s  %s" % (sf, "<<< PURE-FWD-SHAPE" if pf else ""))
