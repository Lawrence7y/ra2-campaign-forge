# -*- coding: utf-8 -*-
"""Final verification: early guards, ③b② branch structure (no eax overwrite,
single QI call), QI callee return bytes. Build verdicts.json with all per-row anchors."""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b3_rows.json"), encoding="utf-8") as f:
    ROWS = json.load(f)["rows"]
with open(os.path.join(HERE, "analysis.json"), encoding="utf-8") as f:
    AN = {x["entry"]: x for x in json.load(f)}
with open(os.path.join(HERE, "gather.json"), encoding="utf-8") as f:
    GD = {x["entry"]: x for x in json.load(f)}
with open(os.path.join(HERE, "ring4.json"), encoding="utf-8") as f:
    R4 = {x["entry"]: x for x in json.load(f)}

QI_CONSTS = {0, 0x80004002, 0x80004003}

def hx(x): return R.hx(x)

def bytes_at(va, n):
    b = R.read_va(va, n)
    return b.hex(" ") if b else ""

def early_guards(insns):
    """Collect mov eax,<imm> where imm is one of the three HRESULT guards."""
    guards = {}
    for i in insns:
        if i.id == X86_INS_MOV and len(i.operands) == 2:
            a, b = i.operands
            if a.type == X86_OP_REG and a.reg == X86_REG_EAX and b.type == X86_OP_IMM:
                v = b.imm & 0xFFFFFFFF
                if v in (0x80070057, 0x80040110, 0x8007000e):
                    guards[hx(v)] = {"addr": hx(i.address), "bytes": i.bytes.hex(" ")}
    return guards

def qi_branch_check(insns, qi_addr):
    """From the `call [eax]` site, verify: mov edi,eax; test edi,edi; jcc; failure-path release."""
    idx = {i.address: k for k, i in enumerate(insns)}
    k = idx.get(int(qi_addr, 16))
    if k is None:
        return None
    seq = insns[k:k+10]
    txt = [(hx(i.address), i.bytes.hex(" "), i.mnemonic + " " + i.op_str) for i in seq]
    # find mov edi,eax / test edi,edi / jge within next 3 insns
    mov_edi = any(i.id == X86_INS_MOV and len(i.operands)==2 and i.operands[0].type==X86_OP_REG
                  and i.operands[0].reg==X86_REG_EDI and i.operands[1].type==X86_OP_REG
                  and i.operands[1].reg==X86_REG_EAX for i in seq[1:4])
    test_edi = any(i.id == X86_INS_TEST and len(i.operands)==2 and i.operands[0].type==X86_OP_REG
                   and i.operands[0].reg==X86_REG_EDI and i.operands[1].type==X86_OP_REG
                   and i.operands[1].reg==X86_REG_EDI for i in seq[1:5])
    jcc = next((i for i in seq[1:6] if i.id in R.JCC_IDS), None)
    # count QI call sites (call [eax] disp0) in whole body -> must be 1
    n_qi = sum(1 for i in insns if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_MEM
               and i.operands[0].mem.base==X86_REG_EAX and i.operands[0].mem.disp==0
               and i.operands[0].mem.index in (X86_REG_INVALID, 0))
    return {"seq": txt, "mov_edi": mov_edi, "test_edi": test_edi,
            "jcc": (jcc.mnemonic + " " + jcc.op_str) if jcc else None,
            "jcc_addr": hx(jcc.address) if jcc else None,
            "n_qi_calls": n_qi}

def qi_callee_bytes(qi_va):
    """Dump the QI function's return instructions with their bytes, for evidence."""
    qva = int(qi_va, 16)
    sz = R.ATLAS.get(hx(qva), {}).get("size") or 128
    rets = []
    for i in R.disasm_body(qva, sz):
        if i.id == X86_INS_RET:
            rets.append((hx(i.address), i.bytes.hex(" "), i.mnemonic + " " + i.op_str))
    return rets

def pick_mainvt(row):
    gd = GD[row["entry"]]
    for oc in gd["qiverify"]:
        for p in oc["vt_cands"]:
            if p["QI_ok"]:
                return oc["obj_ctor"]["dest"], p
    return None, None

def build():
    verdicts = []
    for row in ROWS:
        e = row["entry"]; ea = int(e, 16)
        an = AN[e]; gd = GD[e]; r4 = R4[e]
        insns = list(R.disasm_body(ea, int(row["size"])))
        # ring1
        r1 = an["ring1"]
        # ring2 (first nailed cand)
        c = next(c for c in an["ring2"]["cands"] if c["rtti_name"] and c["slotnum_match"])
        # ring3b
        guards = early_guards(insns)
        branch = qi_branch_check(insns, gd["qi"]["addr"])
        objctor, mainvt = pick_mainvt(row)
        qi_va = mainvt["QI"]
        qirets = qi_callee_bytes(qi_va)
        r3ok = bool(guards and branch and branch["mov_edi"] and branch["test_edi"]
                    and branch["jcc"] and branch["n_qi_calls"] == 1
                    and gd["release"] and mainvt and mainvt["QI_ok"] and qirets)
        # ring4
        r4ok = bool(r4["host_func"] and r4["host_atexit"]==[] and r4["fc_atexit"]==[]
                    and r4["iat_loads"] and r4["reg_call"] and r4["clsid_pushes"]
                    and r4["alloc"] and r4["ctor_call"])
        v = {
            "entry": e, "name": row["name"], "subsystem": row["subsystem"], "size": int(row["size"]),
            "r1": {"in_text": r1["in_text"], "atlas_size": r1["atlas_size"],
                   "n_insn": r1["n_insn"], "n_skipdata": r1["n_skipdata"], "last": r1["last"],
                   "first_bytes": bytes_at(ea, 8)},
            "r2": {"slot_va": c["slot_va"], "slot_bytes": bytes_at(int(c["slot_va"],16),4),
                   "vtable": c["vtable_base"], "slot_off": c["slot_off"], "slotno": c["slotnum_actual"],
                   "clue_slotno": an["ring2"]["slotnum_clue"], "rtti_name": c["rtti_name"],
                   "col": c["col"], "col_bytes": bytes_at(int(c["col"],16),16),
                   "td": c["td"], "td_bytes": bytes_at(int(c["td"],16),16),
                   "name_va": c["name_va"], "name_bytes": bytes_at(int(c["name_va"],16),40)},
            "r3b": {"ok": r3ok, "form": "3b2",
                    "guards": guards, "branch": branch,
                    "qi_site": gd["qi"], "release": gd["release"],
                    "obj_ctor": objctor, "mainvt": mainvt,
                    "qi_va": qi_va, "qi_consts": mainvt["QI_consts"], "qi_nrets": mainvt["QI_nrets"],
                    "qi_rets": qirets,
                    "early_guards_named": {"E_INVALIDARG":"0x80070057","CLASS_E_NOAGGREGATION":"0x80040110","E_OUTOFMEMORY":"0x8007000e"}},
            "r4": {"ok": r4ok, "kind": "live_com_class_object",
                   "factory_ctor": r4["factory_ctor"], "fc_ins": gd["fc_ins"],
                   "fc_callers": r4["fc_callers"], "fc_atexit": r4["fc_atexit"],
                   "host_func": r4["host_func"], "host_size": r4["host_size"],
                   "host_atexit": r4["host_atexit"], "alloc": r4["alloc"],
                   "ctor_call": r4["ctor_call"], "reg_call": r4["reg_call"],
                   "clsid": r4["clsid_pushes"][0][1] if r4["clsid_pushes"] else None,
                   "iat_load": r4["iat_loads"][0] if r4["iat_loads"] else None,
                   "direct_callers_entry": an["direct_callers"]},
        }
        v["all_four"] = bool(r1["in_text"] and r1["n_skipdata"]==0 and c["rtti_name"]
                             and c["slotnum_match"] and r3ok and r4ok)
        verdicts.append(v)
    with open(os.path.join(HERE, "verdicts.json"), "w", encoding="utf-8") as f:
        json.dump(verdicts, f, ensure_ascii=False, indent=1)
    # summary
    r2 = sum(1 for v in verdicts if v["r2"]["rtti_name"] and v["r2"]["slotno"]==v["r2"]["clue_slotno"])
    r3 = sum(1 for v in verdicts if v["r3b"]["ok"])
    r4 = sum(1 for v in verdicts if v["r4"]["ok"])
    af = sum(1 for v in verdicts if v["all_four"])
    print("rows=%d ring2=%d ring3b=%d ring4=%d allfour=%d" % (len(verdicts), r2, r3, r4, af))
    for v in verdicts:
        print("  %s guards=%d mov_edi=%s test_edi=%s %s nQI=%d QI=%s consts=%s nret=%s qi_rets=%d R3=%s R4=%s ALL=%s" % (
            v["entry"], len(v["r3b"]["guards"]), v["r3b"]["branch"]["mov_edi"],
            v["r3b"]["branch"]["test_edi"], v["r3b"]["branch"]["jcc"],
            v["r3b"]["branch"]["n_qi_calls"], v["r3b"]["qi_va"],
            v["r3b"]["qi_consts"], v["r3b"]["qi_nrets"], len(v["r3b"]["qi_rets"]),
            v["r3b"]["ok"], v["r4"]["ok"], v["all_four"]))

if __name__ == "__main__":
    build()
