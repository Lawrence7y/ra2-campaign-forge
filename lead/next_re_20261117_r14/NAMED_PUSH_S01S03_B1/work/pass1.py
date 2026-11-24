# -*- coding: utf-8 -*-
"""第一轮：对 5 个 entry 打印 ①入口 ②虚表/RTTI ③通道A/B ④direct caller 原始发现。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C

ROWS = [
    ("00432050", "S03", "CDFileClass::vslot12", 584),
    ("0065D240", "S03", "CDFileClass::slot15", 101),
    ("0065D3A0", "S03", "RawFileClass::slot0", 124),
    ("007BA530", "S03", "FileStraw::slot2", 93),
    ("007CD80F", "S01", "WinMainCRTStartup", 253),
]

out = []
for eh, sub, name, size in ROWS:
    ea = int(eh, 16)
    rec = {"entry": eh, "sub": sub, "name": name, "size": size}
    # ① entry
    rec["in_text"] = R.in_text(ea)
    ins = R.disasm_body(ea, size)
    rec["n_insn"] = len([i for i in ins if i.id != 0])
    rec["head"] = ["%08X  %s  %s" % (i.address, i.bytes.hex(), i.op_str) for i in ins[:8] if i.id != 0]
    rec["tail"] = ["%08X  %s  %s" % (i.address, i.bytes.hex(), i.op_str) for i in ins[-4:] if i.id != 0]
    # ② refs + slots
    refs = C.find_dword_refs(ea)
    rec["n_refs"] = len(refs)
    rec["refs"] = ["%08X@%s" % (v, s) for v, s in refs[:20]]
    slots = []
    for refva, sec in refs:
        si = C.resolve_slot(refva)
        if si:
            slots.append({k: ("%08X" % v if isinstance(v, int) and k != "slot_off" else v)
                          for k, v in si.items()})
        else:
            slots.append({"refva": "%08X" % refva, "sec": sec, "rtti": None})
    rec["slots"] = slots
    # ③ channel A / B
    chA = R.channel_screen_A(ins)
    chB = R.channel_screen_B(ins)
    rec["chA"] = {"p1": chA["p1"], "p2": chA["p2"], "p3": chA["p3"],
                  "sites": [{k: s[k] for k in ("call_addr", "callee", "test_addr", "test_kind", "test_imm",
                                                "jcc_addr", "jcc_mnemonic", "jcc_target", "p3_form",
                                                "call_site_falsy")} for s in chA["sites"]]}
    rec["chB_tables"] = [{"jmp_addr": t["jmp_addr"], "ncase": t["ncase"], "bound": t["bound"],
                          "table_va": t["table_va"], "ntargets": len(t["targets"])} for t in chB]
    # ④ direct callers
    direct = C.find_direct_calls(ea)
    rec["direct_callers"] = ["%08X" % x for x in direct]
    out.append(rec)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pass1.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
for r in out:
    print("=" * 100)
    print(r["entry"], r["name"], "in_text=", r["in_text"], "n_insn=", r["n_insn"])
    print("  head:", " | ".join(r["head"][:5]))
    print("  refs=", r["n_refs"], r["refs"])
    for s in r["slots"]:
        print("     slot:", s)
    print("  chA p1/p2/p3=", r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"])
    for s in r["chA"]["sites"]:
        print("     site:", s)
    print("  chB tables:", r["chB_tables"])
    print("  direct_callers:", r["direct_callers"])
