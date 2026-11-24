# -*- coding: utf-8 -*-
"""NAMED-PUSH S18 B5 逐行四环取证驱动：复用 recore/witness_core。
只读 gamemd.exe；写域仅本 work 目录。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID,
                          X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG,
                          X86_INS_TEST, X86_OP_REG, X86_REG_EAX)

WORK = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(WORK, "b5_rows.json"), encoding="utf-8"))
ENTRIES = [(r["entry"], r["name"]) for r in data["selected"]]

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def ins_lines(insns, n=None):
    seq = []
    for ins in (insns if n is None else insns[:n]):
        seq.append("%08X: %s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
    return seq

def find_dispatch_sites(slot_off, cap=200000):
    sites = []
    for ins in MD.disasm(R.TEXT_DATA, R.TEXT_VA):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.disp == slot_off and m.base not in (X86_REG_INVALID, 0) and m.index in (X86_REG_INVALID, 0):
                sites.append("%08X" % ins.address)
                if len(sites) >= cap: break
    return sites

def eax_trap_check(insns, sites):
    res = []
    idx = {ins.address: i for i, ins in enumerate(insns)}
    for s in sites:
        ta = int(s["test_addr"], 16) if isinstance(s["test_addr"], str) else s["test_addr"]
        ja = int(s["jcc_addr"], 16) if isinstance(s["jcc_addr"], str) else s["jcc_addr"]
        ti = idx.get(ta); ji = idx.get(ja)
        overwritten = []
        if ti is not None and ji is not None and ji > ti + 1:
            for ins in insns[ti+1:ji]:
                try: _, wr = ins.regs_access()
                except Exception: wr = []
                if X86_REG_EAX in wr:
                    idempotent = (ins.id in (X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG, X86_INS_TEST)
                                  and len(ins.operands) == 2
                                  and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == X86_REG_EAX
                                  and ins.operands[1].type == X86_OP_REG and ins.operands[1].reg == X86_REG_EAX)
                    if not idempotent:
                        overwritten.append("%08X:%s %s" % (ins.address, ins.mnemonic, ins.op_str))
        res.append({"call_addr": s["call_addr"], "test_addr": s["test_addr"],
                    "jcc_addr": s["jcc_addr"], "eax_overwritten": overwritten})
    return res

def analyze_entry(e, hint_name):
    ea = int(e, 16)
    info = R.ATLAS.get(e, {})
    size = info.get("size", 0)
    code = R.read_va(ea, size if size else 512)
    insns = R.disasm(ea, code)
    rec = {
        "entry": e, "hint_name": hint_name, "ea": ea, "atlas": info,
        "in_text": R.in_text(ea),
        "body_end": ea + size,
        "body_end_in_text": R.in_text(ea + size - 1) if size else None,
        "first_insns": ins_lines(insns, 14),
        "last_insns": ins_lines(insns[-8:]) if insns else [],
        "n_insn_disasm": len(insns),
        "n_skipdata": sum(1 for i in insns if i.id == 0),
        "all_insns": ins_lines(insns),
    }
    a = R.channel_screen_A(insns)
    b = R.channel_screen_B(insns)
    rec["chA"] = {k: a[k] for k in ("p1", "p2", "p3")}
    rec["chA_sites"] = a["sites"]
    rec["chA_eax_trap"] = eax_trap_check(insns, a["sites"])
    rec["chB"] = []
    for t in b:
        rec["chB"].append({
            "jmp_addr": "%08X" % t["jmp_addr"], "mnemonic": t["mnemonic"],
            "op_str": t["op_str"], "table_va": ("%08X" % t["table_va"]) if t["table_va"] else None,
            "bound": t["bound"], "ncase": t["ncase"],
            "targets": [{"case": x["case"], "target": "%08X" % x["target"], "slot_va": "%08X" % x["slot_va"]} for x in t["targets"]],
        })
    wit = W.witness_entry(e)
    rec["direct_callers"] = wit["direct_callers"]
    rec["slots"] = wit["slots"]
    for s in rec["slots"]:
        if s.get("rtti_name") and s.get("slot_off") is not None:
            s["dispatch_sites"] = find_dispatch_sites(int(s["slot_off"]))
        else:
            s["dispatch_sites"] = []
    return rec

out = []
for e, nm in ENTRIES:
    r = analyze_entry(e, nm)
    out.append(r)
    nslots_rtti = sum(1 for s in r["slots"] if s.get("rtti_name"))
    print("done %s %-42s A_p3=%d chB=%d slots=%d(rtti=%d) direct=%d" % (
        e, nm, r["chA"]["p3"], len(r["chB"]), len(r["slots"]), nslots_rtti, len(r["direct_callers"])), flush=True)

with open(os.path.join(WORK, "analysis.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote analysis.json (%d rows)" % len(out))
