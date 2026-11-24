# -*- coding: utf-8 -*-
"""S13 B1 ring3b 机械预筛：通道 A(③b② call→test→jcc) + 通道 B(③b① 跳表)。
输出 ring3_scan.json 与 ring3_scan.txt（供人工语义判读，不直接当结论）。
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))

out = {}
for r in ROWS:
    e = r["entry"]
    ea = int(e, 16)
    size = R.ATLAS.get(e, {}).get("size") or 256
    insns = R.disasm_body(ea, size)
    A = R.channel_screen_A(insns)
    B = R.channel_screen_B(insns)
    out[e] = {"name": r["name"], "size": size, "A": A, "B": B}

json.dump(out, open(os.path.join(WORK, "ring3_scan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lines = []
for e, v in out.items():
    A = v["A"]
    lines.append("### %s %s size=%d  A:P1=%d P2=%d P3=%d sites=%d  B:tables=%d" % (
        e, v["name"], v["size"], A["p1"], A["p2"], A["p3"], len(A["sites"]), len(v["B"])))
    for s in A["sites"]:
        lines.append("   A call@%08X -> %s | %s@%08X imm=%s | %s@%08X -> %08X | p3=%s falsy=%s" % (
            s["call_addr"], s["callee"] and ("%08X" % s["callee"]), s["test_kind"], s["test_addr"],
            s["test_imm"], s["jcc_mnemonic"], s["jcc_addr"], s["jcc_target"] or 0,
            s["p3_form"], s["call_site_falsy"]))
        cp = s["callee_profile"]
        lines.append("       callee_consts=%s n_rets=%s origins=%s" % (
            cp["all_consts"], cp["n_rets"], cp["origins"]))
        lines.append("       sig_t=%s sig_f=%s" % (s["sig_taken"], s["sig_fallthrough"]))
    for t in v["B"]:
        lines.append("   B jmp@%08X %s bound=%s table=%08X ncase=%s targets=%d" % (
            t["jmp_addr"], t["op_str"], t["bound"], t["table_va"] or 0,
            t["ncase"], len(t["targets"])))
    lines.append("")
txt = "\n".join(lines)
open(os.path.join(WORK, "ring3_scan.txt"), "w", encoding="utf-8").write(txt)
print(txt)
