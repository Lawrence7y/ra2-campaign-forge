# -*- coding: utf-8 -*-
"""紧凑打印每行 chA 站点：call/callee/test/jcc、两条路径签名、eax 覆写；便于 ③b② 手判。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK = os.path.dirname(os.path.abspath(__file__))
data = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}

def va(x): return int(x, 16) if isinstance(x, str) else int(x)

rows = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))
for row in rows:
    e = row["entry"]
    r = data[e]
    print("=" * 100)
    print("ENTRY %s %s  A_p3=%d chB=%d skipdata=%d" % (e, row["name"], r["chA"]["p3"], len(r["chB"]), r["n_skipdata"]))
    traps = {t["call_addr"]: t["eax_overwritten"] for t in r["chA_eax_trap"]}
    for i, s in enumerate(r["chA_sites"]):
        callee = s.get("callee")
        prof = s.get("callee_profile", {})
        print("  A%d call=%s callee=%s [%s imm=%s] jcc=%s->%s p3form=%s falsy=%s" % (
            i, s["call_addr"], callee or "None(ind)", s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], s["jcc_target"] or "N/A", s["p3_form"], s.get("call_site_falsy")))
        print("      callee_consts=%s all=%s nrets=%s origins=%s" % (
            prof.get("falsifiable_consts"), prof.get("all_consts"), prof.get("n_rets"), prof.get("origins")))
        print("      sig_t=%s" % s["sig_taken"])
        print("      sig_f=%s" % s["sig_fallthrough"])
        ov = traps.get(s["call_addr"], [])
        print("      eax_overwritten=%s" % (ov if ov else 0))
    for b in r["chB"]:
        print("  B jmp=%s table=%s bound=%s ncase=%s targets=%d" % (
            b["jmp_addr"], b["table_va"], b["bound"], b["ncase"], len(b["targets"])))
