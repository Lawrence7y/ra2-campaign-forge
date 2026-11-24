# -*- coding: utf-8 -*-
"""紧凑汇总：每行每站点的 ③b② 可判定要素，输出 _work/sites.tsv（UTF-8）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
AN = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
out = open(os.path.join(WORK, "sites.tsv"), "w", encoding="utf-8")
cols = ["entry", "name", "call", "callee", "test", "imm", "jcc", "target",
        "callee_consts", "callee_nrets", "callee_origins", "falsifiable_callee",
        "caller_imm_falsifiable", "eax_clobber", "taken_sig", "fall_sig", "true_diff"]
print("\t".join(cols), file=out)

def clobber(insns, t, j):
    for ins in insns:
        if t < ins.address < j:
            if ins.id == X86_INS_CALL:
                return "CALL"
            if ins.operands and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == X86_REG_EAX:
                return "%08X:%s" % (ins.address, ins.mnemonic)
    return "-"

for rec in AN:
    entry = rec["entry"]
    size = rec["ring1"].get("atlas_size") or 512
    insns = R.disasm(int(entry, 16), R.read_va(int(entry, 16), size))
    for s in (rec.get("chA") or {}).get("sites", []):
        cp = s["callee_profile"]
        fals = [c for c in cp.get("all_consts", []) if R.is_falsifiable(int(c, 16))]
        row = [entry, rec["name"], "%08X" % s["call_addr"],
               "%08X" % s["callee"] if s["callee"] else "-",
               s["test_kind"], str(s["test_imm"]),
               "%s@%08X" % (s["jcc_mnemonic"], s["jcc_addr"]),
               "%08X" % s["jcc_target"] if s["jcc_target"] else "-",
               ",".join(cp.get("all_consts") or []), str(cp.get("n_rets")),
               str(cp.get("origins")), ",".join(fals) or "-",
               str(s["call_site_falsy"]), clobber(insns, s["test_addr"], s["jcc_addr"]),
               str(s["sig_taken"]["calls"]) + "/ret" + str(s["sig_taken"]["rets"]) + "/" + str(s["sig_taken"]["has_ret"]),
               str(s["sig_fallthrough"]["calls"]) + "/ret" + str(s["sig_fallthrough"]["rets"]) + "/" + str(s["sig_fallthrough"]["has_ret"]),
               "Y"]
        print("\t".join(row), file=out)
out.close()
print(open(os.path.join(WORK, "sites.tsv"), encoding="utf-8").read().count("\n"), "lines")
