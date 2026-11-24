# -*- coding: utf-8 -*-
"""环③ 机械预筛：18 行内 ③b② 站点与 ③b① 跳表。输出每行候选站点清单。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))

out = {}
for i, r in enumerate(rows, 1):
    e, insns = C.disasm_body(r["entry"])
    nskip = sum(1 for x in insns if x.id == 0)
    sites = C.sites_3b2(insns)
    jts = C.jumptables(insns)
    diff = [s for s in sites if s["differ"]]
    rec = dict(entry=r["entry"], name=r["name"], size=int(r["size"]),
               n_insn=len(insns), n_skip=nskip, n_sites=len(sites), n_diff=len(diff),
               sites=diff[:12], n_jt=len(jts), jts=jts[:4])
    out[r["entry"]] = rec
    print("%2d %s %-24s insn=%-5d skip=%-3d ③b②站点=%-3d 两路不同=%-3d ③b①表=%d" %
          (i, r["entry"], r["name"], len(insns), nskip, len(sites), len(diff), len(jts)))
    for s in diff[:12]:
        print("      call %08X -> %s | %s@%08X imm=%s | %s@%08X -> %08X" %
              (s["call_va"], ("%08X" % s["callee"]) if s["callee"] else "?",
               s["test_kind"], s["test_va"],
               ("0x%X" % s["test_imm"]) if s["test_imm"] is not None else "-",
               s["jcc_mn"], s["jcc_va"], s["jcc_target"] or 0))

json.dump(out, open(os.path.join(here, "ring3_scan.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
