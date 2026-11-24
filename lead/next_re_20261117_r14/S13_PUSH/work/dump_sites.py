# -*- coding: utf-8 -*-
"""Dump channel-A hit sites in full + looser jump-table scan over pool."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
screen = json.load(open(os.path.join(WORK, "screen.json"), encoding="utf-8"))
a_hits = [r for r in screen if r["A_hit"]]

print("=== Channel A sites (13 candidates) ===")
for r in a_hits:
    print("\n### %s %s %s (size=%s n_insn=%d)" % (r["entry"], r["grade"], r["name"], r["atlas_size"], r["n_insn"]))
    for s in r["A_sites"]:
        print("  call %s @%08X | %s imm=%s | %s @%08X -> %s" % (
            ("%08X"%s["callee"]) if s["callee"] else "None", s["call_addr"],
            s["test_kind"], s["test_imm"], s["jcc_mnemonic"], s["jcc_addr"],
            ("%08X"%s["jcc_target"]) if s["jcc_target"] else "None"))
        print("     form=%s call_site_falsy=%s callee=%s" % (
            s["p3_form"], s["call_site_falsy"], s["callee_profile"]["callee_key"]))
        print("     sig_taken=%s" % s["sig_taken"])
        print("     sig_fall  =%s" % s["sig_fallthrough"])

print("\n\n=== Looser jump-table scan over ALL pool (any FF /4 mem jmp) ===")
pool = json.load(open(os.path.join(WORK, "pool.json"), encoding="utf-8"))
for p in pool:
    ea = int(p["entry"], 16)
    insns = R.disasm_body(ea, p["atlas_size"])
    for ins in insns:
        if ins.id == X86_INS_JMP and ins.operands and ins.operands[0].type == X86_OP_MEM:
            op = ins.operands[0].mem
            if op.scale in (2,4,8):
                print("  %s jmp@%08X scale=%d base=%s index=%s disp=%s op=%s" % (
                    p["entry"], ins.address, op.scale,
                    ins.reg_name(op.base) if op.base else None,
                    ins.reg_name(op.index) if op.index else None,
                    hex(op.disp), ins.op_str))
