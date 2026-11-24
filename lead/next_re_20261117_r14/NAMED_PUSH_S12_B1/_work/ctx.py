# -*- coding: utf-8 -*-
"""对每行每个"两路动作不同"的 ③b② 站点，打印 call 前 4 条到 jcc 后 14 条的上下文。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))
out = []


def ctx(insns, call_va):
    idx = [k for k, i in enumerate(insns) if i.address == call_va]
    if not idx:
        return []
    k = idx[0]
    lines = []
    for j in range(max(0, k - 4), min(len(insns), k + 15)):
        ins = insns[j]
        mark = ">>>>" if ins.address == call_va else "    "
        lines.append("%s %08X: %-30s" % (mark, ins.address, ins.mnemonic + " " + ins.op_str))
    return lines


for r in rows:
    e, insns = C.disasm_body(r["entry"])
    sites = [s for s in C.sites_3b2(insns) if s["differ"]]
    out.append("=" * 100)
    out.append("ROW %s  %s  size=%s  n_insn=%d  n_diff_sites=%d" %
               (r["entry"], r["name"], r["size"], len(insns), len(sites)))
    for s in sites:
        callee = ("%08X" % s["callee"]) if s["callee"] else "((INDIRECT))"
        out.append("-- 站点 call@%08X -> %s | %s imm=%s | %s@%08X -> %s" %
                   (s["call_va"], callee, s["test_kind"],
                    ("0x%X" % s["test_imm"]) if s["test_imm"] is not None else "-",
                    s["jcc_mn"], s["jcc_va"],
                    ("%08X" % s["jcc_target"]) if s["jcc_target"] else "?"))
        for line in ctx(insns, s["call_va"]):
            out.append("   " + line)
        out.append("")

txt = "\n".join(out)
open(os.path.join(here, "sites_ctx.txt"), "w", encoding="utf-8").write(txt)
print("wrote sites_ctx.txt %d lines" % len(out))
