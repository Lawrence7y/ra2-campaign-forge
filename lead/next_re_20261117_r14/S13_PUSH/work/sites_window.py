# -*- coding: utf-8 -*-
"""逐候选导出 call/test/jcc 附近的指令窗口，人工核对环③（含 eax 覆写陷阱）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
screen = json.load(open(os.path.join(WORK, "screen.json"), encoding="utf-8"))
a_hits = [r for r in screen if r["A_hit"]]

lines = []
def w(s=""):
    lines.append(s)
    print(s)

for r in a_hits:
    ea = int(r["entry"], 16)
    insns = R.disasm_body(ea, r["atlas_size"])
    idx = {ins.address: i for i, ins in enumerate(insns)}
    w("="*90)
    w("### %s %s %s (size=%d n_insn=%d)" % (r["entry"], r["grade"], r["name"], r["atlas_size"], r["n_insn"]))
    # 序言/边界：首 4 条
    w("  prologue:")
    for ins in insns[:5]:
        w("    %08X: %-10s %s" % (ins.address, ins.mnemonic, ins.op_str))
    for s in r["A_sites"]:
        ca = s["call_addr"]
        ci = idx.get(ca)
        w("  --- site call@%08X callee=%s form=%s ---" % (ca, ("%08X"%s["callee"]) if s["callee"] else "None", s["p3_form"]))
        if ci is not None:
            for j in range(max(0, ci-1), min(len(insns), ci+16)):
                ins = insns[j]
                mark = ""
                if ins.address == s["call_addr"]: mark = " <<< CALL"
                elif ins.address == s["test_addr"]: mark = " <<< TEST/CMP"
                elif ins.address == s["jcc_addr"]: mark = " <<< JCC"
                elif ins.address == s["jcc_target"]: mark = " <<< FAIL_TARGET"
                w("    %08X: %-10s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))

open(os.path.join(WORK, "sites_window.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("\nwrote sites_window.txt")
