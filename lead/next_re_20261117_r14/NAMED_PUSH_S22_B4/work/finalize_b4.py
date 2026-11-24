# -*- coding: utf-8 -*-
"""B4 final verdict with the two batch-specific constraints:
   (C1) ②: object's MAIN vtable slot0 must be 0x00410260 (not a small member table).
   (C2) ④: anchor must NOT be in a destructor (atexit/dtor) -> FAIL (㉓).
Builds verdicts.json with all per-row anchors. Read-only on target.
"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b4_rows.json"), encoding="utf-8") as f:
    ROWS = json.load(f)["rows"]
with open(os.path.join(HERE, "analysis.json"), encoding="utf-8") as f:
    AN = {x["entry"]: x for x in json.load(f)}
with open(os.path.join(HERE, "gather.json"), encoding="utf-8") as f:
    GD = {x["entry"]: x for x in json.load(f)}

MAIN_QI = 0x00410260
QI_CONSTS = {0, 0x80004002, 0x80004003}

def hx(x): return R.hx(x)
def bytes_at(va, n):
    b = R.read_va(va, n)
    return b.hex(" ") if b else ""

def early_guards(insns):
    guards = {}
    for i in insns:
        if i.id == X86_INS_MOV and len(i.operands)==2:
            a,b = i.operands
            if a.type==X86_OP_REG and a.reg==X86_REG_EAX and b.type==X86_OP_IMM:
                v = b.imm & 0xFFFFFFFF
                if v in (0x80070057,0x80040110,0x8007000e):
                    guards[hx(v)] = {"addr":hx(i.address),"bytes":i.bytes.hex(" ")}
    return guards

def qi_branch_check(insns, qi_addr):
    idx = {i.address:k for k,i in enumerate(insns)}
    k = idx.get(int(qi_addr,16))
    if k is None: return None
    seq = insns[k:k+10]
    txt = [(hx(i.address), i.bytes.hex(" "), i.mnemonic+" "+i.op_str) for i in seq]
    mov_edi = any(i.id==X86_INS_MOV and len(i.operands)==2 and i.operands[0].type==X86_OP_REG
                  and i.operands[0].reg==X86_REG_EDI and i.operands[1].type==X86_OP_REG
                  and i.operands[1].reg==X86_REG_EAX for i in seq[1:4])
    test_edi = any(i.id==X86_INS_TEST and len(i.operands)==2 and i.operands[0].type==X86_OP_REG
                   and i.operands[0].reg==X86_REG_EDI and i.operands[1].type==X86_OP_REG
                   and i.operands[1].reg==X86_REG_EDI for i in seq[1:5])
    jcc = next((i for i in seq[1:6] if i.id in R.JCC_IDS), None)
    n_qi = sum(1 for i in insns if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_MEM
               and i.operands[0].mem.base==X86_REG_EAX and i.operands[0].mem.disp==0
               and i.operands[0].mem.index in (X86_REG_INVALID,0))
    return {"seq":txt,"mov_edi":mov_edi,"test_edi":test_edi,
            "jcc":(jcc.mnemonic+" "+jcc.op_str) if jcc else None,
            "jcc_addr":hx(jcc.address) if jcc else None,"n_qi_calls":n_qi}

def qi_callee_bytes(qi_va):
    if not qi_va: return []
    qva = int(qi_va,16)
    sz = R.ATLAS.get(hx(qva),{}).get("size") or 128
    return [(hx(i.address), i.bytes.hex(" "), i.mnemonic+" "+i.op_str)
            for i in R.disasm_body(qva,sz) if i.id==X86_INS_RET]

def build():
    verdicts = []
    for row in ROWS:
        e = row["entry"]; ea = int(e,16)
        an = AN[e]; gd = GD[e]
        insns = list(R.disasm_body(ea,int(row["size"])))
        r1 = an["ring1"]
        c = next(c for c in an["ring2"]["cands"] if c["rtti_name"] and c["slotnum_match"])

        # ---- pick QI candidate ----
        # Prefer the candidate whose vt slot0 == MAIN_QI (canonical main vtable).
        mainvt = None; objctor = None; picked_kind = None
        all_cands = [(oc["obj_ctor"]["dest"], p) for oc in gd["qiverify"] for p in oc["vt_cands"]]
        canonical = [(o,p) for o,p in all_cands if p["QI"] and int(p["QI"],16)==MAIN_QI]
        if canonical:
            objctor, mainvt = canonical[0]; picked_kind = "main_slot0_410260"
        else:
            hrt = [(o,p) for o,p in all_cands if p["QI_ok"]]
            if hrt:
                objctor, mainvt = hrt[0]; picked_kind = "hresult_but_not_410260"
            elif all_cands:
                objctor, mainvt = all_cands[0]; picked_kind = "no_falsifiable_qi"
        qi_va = mainvt["QI"] if mainvt else None

        # ---- C1: ② main-vt slot0 constraint ----
        r2_rtti_ok = bool(c["rtti_name"] and c["slotnum_match"])
        mainvt_slot0_ok = bool(mainvt and qi_va and int(qi_va,16)==MAIN_QI)
        ring2_ok = bool(r2_rtti_ok and mainvt_slot0_ok)  # ② incl. batch constraint

        # ---- ③b ----
        guards = early_guards(insns)
        branch = qi_branch_check(insns, gd["qi"]["addr"]) if gd["qi"] else None
        qirets = qi_callee_bytes(qi_va)
        r3ok = bool(guards and branch and branch["mov_edi"] and branch["test_edi"]
                    and branch["jcc"] and branch["n_qi_calls"]==1
                    and gd["release"] and mainvt and mainvt["QI_ok"] and qirets)

        # ---- C2: ④ anchor not in destructor ----
        # ring4.json not loaded here; recompute minimal anchor checks from gather + core2
        fc = int(gd["factory_ctor"],16)
        fc_atexit = C.is_atexit_registered(fc)
        reg = gd["reg_sites"][0] if gd["reg_sites"] else None
        ctor_call = int(reg["ctor_call"],16) if reg else None
        from core2 import find_containing_atlas_func
        host = find_containing_atlas_func(ctor_call) if ctor_call else None
        host_va = host[0] if host else None
        host_size = R.ATLAS.get(hx(host_va),{}).get("size") if host_va else None
        host_atexit = C.is_atexit_registered(host_va) if host_va else None
        anchor_in_dtor = bool((fc_atexit) or (host_atexit))
        r4ok = bool(reg and host_va and not anchor_in_dtor and gd["fc_callers"])

        v = {
            "entry":e,"name":row["name"],"subsystem":row["subsystem"],"size":int(row["size"]),
            "r1":{"in_text":r1["in_text"],"atlas_size":r1["atlas_size"],"n_insn":r1["n_insn"],
                  "n_skipdata":r1["n_skipdata"],"last":r1["last"],"first_bytes":bytes_at(ea,8)},
            "r2":{"slot_va":c["slot_va"],"slot_bytes":bytes_at(int(c["slot_va"],16),4),
                  "vtable":c["vtable_base"],"slot_off":c["slot_off"],"slotno":c["slotnum_actual"],
                  "clue_slotno":an["ring2"]["slotnum_clue"],"rtti_name":c["rtti_name"],
                  "col":c["col"],"col_bytes":bytes_at(int(c["col"],16),16),
                  "td":c["td"],"td_bytes":bytes_at(int(c["td"],16),16),
                  "name_va":c["name_va"],"name_bytes":bytes_at(int(c["name_va"],16),44),
                  "rtti_ok":r2_rtti_ok},
            "special_C1":{"mainvt_slot0_required":hx(MAIN_QI),
                          "mainvt_slot0_actual":qi_va,
                          "ok":mainvt_slot0_ok,"picked_kind":picked_kind},
            "r3b":{"ok":r3ok,"form":"3b2","guards":guards,"branch":branch,
                   "qi_site":gd["qi"],"release":gd["release"],
                   "obj_ctor":objctor,"mainvt":mainvt,"qi_va":qi_va,
                   "qi_consts":mainvt["QI_consts"] if mainvt else [],
                   "qi_nrets":mainvt["QI_nrets"] if mainvt else None,
                   "qi_rets":qirets,
                   "mainvt_writes":all_cands},
            "r4":{"ok":r4ok,"kind":"live_com_class_object",
                  "factory_ctor":gd["factory_ctor"],"fc_ins":gd["fc_ins"],
                  "fc_callers":gd["fc_callers"],"fc_atexit":fc_atexit,
                  "host_func":hx(host_va) if host_va else None,"host_size":host_size,
                  "host_atexit":host_atexit,"anchor_in_dtor":anchor_in_dtor,
                  "ctor_call":hx(ctor_call) if ctor_call else None,
                  "direct_callers_entry":an["direct_callers"]},
        }
        v["all_four"] = bool(r1["in_text"] and r1["n_skipdata"]==0 and ring2_ok and r3ok and r4ok)
        verdicts.append(v)

    with open(os.path.join(HERE,"verdicts.json"),"w",encoding="utf-8") as f:
        json.dump(verdicts,f,ensure_ascii=False,indent=1)

    r2 = sum(1 for v in verdicts if v["r2"]["rtti_ok"] and v["special_C1"]["ok"])
    r2rtti = sum(1 for v in verdicts if v["r2"]["rtti_ok"])
    c1 = sum(1 for v in verdicts if v["special_C1"]["ok"])
    r3 = sum(1 for v in verdicts if v["r3b"]["ok"])
    r4 = sum(1 for v in verdicts if v["r4"]["ok"])
    af = sum(1 for v in verdicts if v["all_four"])
    print("rows=%d r2rtti=%d C1(mainvt410260)=%d ring2(②inclC1)=%d ring3b=%d ring4=%d allfour=%d" % (
        len(verdicts),r2rtti,c1,r2,r3,r4,af))
    for v in verdicts:
        print("  %s %-48s C1=%s(QI=%s,%s) R3=%s R4=%s(dtor=%s) ALL=%s" % (
            v["entry"],v["name"][:48],v["special_C1"]["ok"],v["special_C1"]["mainvt_slot0_actual"],
            v["special_C1"]["picked_kind"],v["r3b"]["ok"],v["r4"]["ok"],
            v["r4"]["anchor_in_dtor"],v["all_four"]))

if __name__=="__main__":
    build()
