# -*- coding: utf-8 -*-
"""第一遍全量分析：对 6 个候选做 ①边界 ②vtable/RTTI ③b预筛 ④direct/witness 扫描。
输出 work/pass1.json + work/pass1.txt（只描述事实，不下最终裁定）。
"""
import json, sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

CANDS = [
    ("004A2B60", 360, "CStreamClass::slot3", 3),
    ("004A2CD0", 302, "CStreamClass::slot4", 4),
    ("00539AE0", 956, "Load_StreamFields", None),
    ("0055AAC0", 122, "Load_SwizzledObject", None),
    ("006BEF10", 114, "T_TClassFactory_VCStreamClass__::slot3", 3),
    ("006BF690", 117, "T_TClassFactory_VSuperClass__::slot3", 3),
]

def analyze(entry_hex, size, name, slot_hint):
    ea = int(entry_hex, 16)
    insns = C.disasm_body(ea, size)
    n_skip = sum(1 for i in insns if i.id == 0)
    # last insn
    last = insns[-1] if insns else None
    # direct calls into entry
    direct = C.find_direct_calls(ea)
    # dword refs (vtable slot candidates) outside .text
    refs = C.find_dword_refs(ea)
    slots = []
    for refva, sec in refs:
        si = C.resolve_slot(refva, kmax=64)
        slots.append({"slot_va": C.hx(refva), "section": sec,
                      "resolved": si and {
                          "vtable_base": C.hx(si["vtable_base"]),
                          "slot_off": si["slot_off"], "slot_idx": si["slot_idx"],
                          "col": C.hx(si["col"]), "td": C.hx(si["td"]),
                          "rtti_name": si["rtti_name"]}})
    # channel A (strict + loose)
    chA_strict = C.channel_A(insns, strict=True)
    chA_loose = C.channel_A(insns, strict=False)
    # memory writes inside body (non-stack)
    mem_writes = []
    for ins in insns:
        if ins.id == 0: continue
        for op in ins.operands:
            if op.type == C.X86_OP_MEM:
                # detect write: capstone doesn't give direction directly; use id heuristics
                pass
    return {
        "entry": entry_hex, "name": name, "size": size, "slot_hint": slot_hint,
        "in_text": C.in_text(ea), "n_insn": len(insns), "n_skip": n_skip,
        "first_bytes": C.va_read(ea, 16).hex(" ").upper(),
        "last": {"addr": C.hx(last.address), "mnem": last.mnemonic, "op": last.op_str,
                 "bytes": last.bytes.hex().upper()} if last else None,
        "direct_callers_n": len(direct), "direct_callers": [C.hx(x) for x in direct[:30]],
        "dword_refs_n": len(refs), "slots": slots,
        "chA_strict": chA_strict, "chA_loose": chA_loose,
    }

def main():
    out = {"entries": []}
    lines = []
    for e, sz, nm, sh in CANDS:
        r = analyze(e, sz, nm, sh)
        out["entries"].append(r)
        lines.append("=== %s %s size=%d ===" % (e, nm, sz))
        lines.append("in_text=%s n_insn=%d n_skip=%d first=%s last=%s %s %s" %
                     (r["in_text"], r["n_insn"], r["n_skip"], r["first_bytes"],
                      r["last"]["addr"], r["last"]["mnem"], r["last"]["op"]))
        lines.append("direct_callers=%d %s" % (r["direct_callers_n"], " ".join(r["direct_callers"][:15])))
        lines.append("dword_refs=%d" % r["dword_refs_n"])
        for s in r["slots"]:
            if s["resolved"]:
                rr = s["resolved"]
                lines.append("  slot@%s [%s] vt=%s off=%s idx=%s col=%s td=%s name=%s" %
                             (s["slot_va"], s["section"], rr["vtable_base"], rr["slot_off"],
                              rr["slot_idx"], rr["col"], rr["td"], rr["rtti_name"]))
            else:
                lines.append("  slot@%s [%s] UNRESOLVED" % (s["slot_va"], s["section"]))
        lines.append("chA_strict=%d chA_loose=%d" % (len(r["chA_strict"]), len(r["chA_loose"])))
        for s in r["chA_strict"]:
            lines.append("  [strict] call@%s %s@%s imm=%s jcc=%s@%s tgt=%s falsy=%s t=%s f=%s" %
                         (s["call_addr"], s["test_kind"], s["test_addr"], s["test_imm"],
                          s["jcc"], s["jcc_addr"], s["jcc_target"], s["falsy"],
                          s["sig_taken"]["rets"], s["sig_fallthrough"]["rets"]))
        for s in r["chA_loose"]:
            if s in r["chA_strict"]: continue
            lines.append("  [loose] call@%s %s@%s imm=%s jcc=%s@%s falsy=%s t=%s f=%s" %
                         (s["call_addr"], s["test_kind"], s["test_addr"], s["test_imm"],
                          s["jcc"], s["jcc_addr"], s["falsy"],
                          s["sig_taken"]["rets"], s["sig_fallthrough"]["rets"]))
        lines.append("")
    txt = "\n".join(lines)
    with open("pass1.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open("pass1.txt", "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)

if __name__ == "__main__":
    main()
