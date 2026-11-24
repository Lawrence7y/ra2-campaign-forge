# -*- coding: utf-8 -*-
"""Per-row gather for S22 B2 factory slot3 rows.
For each of the 18 rows, auto-discover:
  - ring3b②: QI site (call [eax] disp0), release site (call [edx+0x20]),
    object ctor (direct call != operator-new), and among the object ctor's
    offset0 vtable writes, pick the one whose vt[0]=QueryInterface returns the
    falsifiable HRESULT constant set {0,0x80004002,0x80004003}.
  - ring4: factory ctor (entry-0xD0), its offset0 write of the factory vt,
    its callers + atexit check, and the registration site in the host function
    (push <factory>; push <CLSID>; call CoRegisterClassObject).
Read-only on the target binary.
"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b3_rows.json"), encoding="utf-8") as f:
    ROWS = json.load(f)["rows"]

NEW = 0x7C8E17   # operator new
QI_CONSTS = {0, 0x80004002, 0x80004003}

def hx(x): return R.hx(x)

def bytes_at(va, n):
    b = R.read_va(va, n)
    return b.hex(" ") if b else ""

def insn_seq(insns, start_idx, count):
    return [(hx(insns[j].address), insns[j].bytes.hex(" "), insns[j].mnemonic + " " + insns[j].op_str)
            for j in range(start_idx, min(start_idx + count, len(insns)))]

def obj_main_vt_candidates(ctor_va):
    """All mov [reg+0], imm with imm in vt range, within the ctor body."""
    sz = R.ATLAS.get(hx(ctor_va), {}).get("size") or 1024
    cands = []
    for ins in R.disasm_body(ctor_va, sz):
        if ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if a.type == X86_OP_MEM and b.type == X86_OP_IMM and a.mem.disp == 0 and a.mem.scale == 1:
                v = b.imm & 0xFFFFFFFF
                if 0x7E0000 <= v <= 0x7FC000:
                    cands.append({"write": hx(ins.address), "vt": hx(v),
                                  "insn": ins.bytes.hex(" ") + " " + ins.mnemonic + " " + ins.op_str})
    return cands

def pick_qi(cands):
    """Among candidate main-vt writes, pick vt whose slot0 QI returns the falsifiable HRESULT set."""
    out = []
    for c in cands:
        vt = int(c["vt"], 16)
        qva = R.u32(vt)
        prof = R.callee_return_profile(qva) if qva else None
        consts = sorted(prof["consts"]) if prof else []
        qi_ok = bool(prof and set(consts) == QI_CONSTS and prof["n_rets"] >= 2)
        out.append({"write": c["write"], "vt": c["vt"], "insn": c["insn"],
                    "QI": hx(qva) if qva else None,
                    "QI_consts": [hx(x) for x in consts],
                    "QI_nrets": prof["n_rets"] if prof else None,
                    "QI_ok": qi_ok})
    return out

def find_release_call(insns):
    for k, i in enumerate(insns):
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_MEM \
           and i.operands[0].mem.disp == 0x20:
            return {"addr": hx(i.address), "bytes": i.bytes.hex(" "), "op": i.mnemonic + " " + i.op_str,
                    "seq": insn_seq(insns, k, 2)}
    return None

def find_qi_call(insns):
    for k, i in enumerate(insns):
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_MEM \
           and i.operands[0].mem.base == X86_REG_EAX and i.operands[0].mem.disp == 0 \
           and i.operands[0].mem.index in (X86_REG_INVALID, 0):
            return {"addr": hx(i.address), "bytes": i.bytes.hex(" "), "seq": insn_seq(insns, k, 9)}
    return None

def find_obj_ctor(insns):
    """Direct call in body that is not operator-new; the object constructor."""
    calls = []
    for k, i in enumerate(insns):
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            dest = i.operands[0].imm & 0xFFFFFFFF
            calls.append({"addr": hx(i.address), "dest": hx(dest), "bytes": i.bytes.hex(" ")})
    objcalls = [c for c in calls if int(c["dest"], 16) != NEW]
    return objcalls

def find_reg_site(factory_ctor_va):
    """Find in .text the site `push <factory_ctor>` followed shortly by call <factory_ctor>,
    with preceding allocation (`push 8; call new`) and following reg via CoRegisterClassObject.
    We scan for the `call <factory_ctor>` (E8 rel32) and read backward/forward context.
    """
    needle_dest = factory_ctor_va
    sites = []
    text = R.TEXT_DATA
    for off in range(0, len(text) - 5):
        if text[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", text, off + 1)[0]
        dest = (R.TEXT_VA + off + 5 + rel) & 0xFFFFFFFF
        if dest != needle_dest:
            continue
        callva = R.TEXT_VA + off
        # disassemble a window around it to find push 8; call new (alloc) and push <CLSID>
        start = max(0, off - 40)
        window = text[start:off + 60]
        wins = []
        for i in R.disasm(R.TEXT_VA + start, window):
            wins.append({"addr": hx(i.address), "bytes": i.bytes.hex(" "), "text": i.mnemonic + " " + i.op_str})
        sites.append({"ctor_call": hx(callva), "window": wins})
    return sites

def analyze_row(row):
    ea = int(row["entry"], 16)
    name = row["name"]
    size = int(row["size"])
    # --- object ctor / QI / release from body ---
    insns = list(R.disasm_body(ea, size))
    qi = find_qi_call(insns)
    rel = find_release_call(insns)
    objcalls = find_obj_ctor(insns)
    qiverify = []
    for oc in objcalls:
        cands = obj_main_vt_candidates(int(oc["dest"], 16))
        picks = pick_qi(cands)
        qiverify.append({"obj_ctor": oc, "vt_cands": picks})
    # --- factory ctor ---
    fc = ea - 0xD0
    fc_ins = [(hx(i.address), i.bytes.hex(" "), i.mnemonic + " " + i.op_str)
              for i in R.disasm_body(fc, 20)]
    fc_atexit = C.is_atexit_registered(fc)
    fc_callers = [hx(x) for x in C.find_direct_calls(fc)]
    # factory ctor offset0 write
    fc_vt_writes = []
    for a, b, op in fc_ins:
        if "mov dword ptr [eax], 0x" in op or ("mov dword ptr [eax]" in op and "imm" not in op):
            fc_vt_writes.append((a, b, op))
    # registration sites
    reg = find_reg_site(fc)
    return {
        "entry": row["entry"], "name": name, "size": size,
        "qi": qi, "release": rel, "obj_ctor_calls": objcalls, "qiverify": qiverify,
        "factory_ctor": hx(fc), "fc_ins": fc_ins, "fc_atexit": fc_atexit,
        "fc_callers": fc_callers, "fc_vt_writes": fc_vt_writes,
        "reg_sites": reg,
    }

def main():
    out = [analyze_row(r) for r in ROWS]
    with open(os.path.join(HERE, "gather.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    # concise summary
    for r in out:
        ok_qi = [p for oc in r["qiverify"] for p in oc["vt_cands"] if p["QI_ok"]]
        print("%s QI@%s rel@%s objcalls=%s qi_ok=%d fc=%s fc_atexit=%s fc_callers=%s reg_sites=%d" % (
            r["entry"],
            r["qi"]["addr"] if r["qi"] else "-",
            r["release"]["addr"] if r["release"] else "-",
            [c["dest"] for c in r["obj_ctor_calls"]],
            len(ok_qi), r["factory_ctor"], r["fc_atexit"], r["fc_callers"],
            len(r["reg_sites"])))
        for oc in r["qiverify"]:
            for p in oc["vt_cands"]:
                print("    objctor=%s write@%s vt=%s QI=%s consts=%s nret=%s ok=%s" % (
                    oc["obj_ctor"]["dest"], p["write"], p["vt"], p["QI"], p["QI_consts"], p["QI_nrets"], p["QI_ok"]))

if __name__ == "__main__":
    main()
