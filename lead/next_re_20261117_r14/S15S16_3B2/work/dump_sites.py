# -*- coding: utf-8 -*-
"""Dump P1/P2/P3 site details for sanity check."""
import json, os
WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15S16_3B2\work"
res = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
for r in res:
    if r["p1_count"] == 0:
        continue
    print(f"\n=== {r['entry']} {r['subsystem']} {r['name']} size={r['atlas_size']} insns={r['n_insn']} ===")
    for i, s in enumerate(r["p1"]):
        cal = s["callee"]
        print(f"  P1[{i}] call@{s['call_addr']:08X} -> {cal:08X}" if cal else f"  P1[{i}] call@{s['call_addr']:08X} -> indirect",
              f"| test@{s['test_addr']:08X} {s['test_kind']}(imm={s['test_imm']})",
              f"| jcc@{s['jcc_addr']:08X} {s['jcc_mnemonic']} -> {s['jcc_target']} ft={s['fallthrough']}")
        if "sig_taken" in s:
            st, sf = s["sig_taken"], s["sig_fallthrough"]
            print(f"        P2 YES taken={st} fallthrough={sf}")
            if "callee_rets" in s:
                print(f"        P3 YES callee_rets={[hex(x) for x in s['callee_rets']]}")
            else:
                print(f"        P3 no (callee_rets not falsifiable)")
        else:
            print(f"        P2 no")
