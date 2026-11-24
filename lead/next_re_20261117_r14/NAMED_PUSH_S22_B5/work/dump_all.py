# -*- coding: utf-8 -*-
"""Dump full analysis for the 9 S22 B5 vector rows: disasm, vtable/RTTI refs, slot, direct callers, writes, channel A/B.
只读目标，输出 intermediate JSON + 可读 dump。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b5_rows.json"), encoding="utf-8") as f:
    rows = json.load(f)

ALL = {}
for r in rows:
    entry = r["entry"]
    ea = int(entry, 16)
    size = int(r["size"])
    insns = R.disasm_body(ea, size)

    # skipdata check + last insn
    n_skip = sum(1 for i in insns if i.id == 0)
    last = insns[-1] if insns else None
    last_txt = ("%s %s" % (last.mnemonic, last.op_str)) if last else None

    # ① atlas boundary
    atlas = R.ATLAS.get(entry)

    # ② vtable refs + RTTI + slot
    refs = C.find_dword_refs(ea)
    slots = []
    for refva, sec in refs:
        si = C.resolve_slot(refva)
        if si is None:
            slots.append({"slot_va": "%08X" % refva, "section": sec, "rtti": None})
        else:
            slots.append({
                "slot_va": "%08X" % refva, "section": sec,
                "vtable_base": "%08X" % si["vtable_base"], "slot_off": si["slot_off"],
                "slot_no": si["slot_off"] // 4,
                "col": "%08X" % si["col"], "td": "%08X" % si["td"],
                "name_va": "%08X" % si["name_va"], "rtti_name": si["rtti_name"],
            })

    # ④ direct callers
    direct = C.find_direct_calls(ea)

    # channel A/B
    chA = R.channel_screen_A(insns)
    chB = R.channel_screen_B(insns)

    # full disasm text
    dis = []
    for i in insns:
        dis.append("%08X  %-20s %s" % (i.address, (i.bytes.hex()), ("%s %s" % (i.mnemonic, i.op_str)).strip()))

    ALL[entry] = {
        "name": r["name"], "size": size, "n_insn": len(insns), "n_skipdata": n_skip,
        "last_insn": last_txt, "atlas": atlas,
        "slots": slots, "direct_callers": ["%08X" % x for x in direct],
        "chA": chA, "chB": chB, "disasm": dis,
    }

with open(os.path.join(HERE, "dump.json"), "w", encoding="utf-8") as f:
    json.dump(ALL, f, ensure_ascii=False, indent=1)

# concise summary to stdout
for entry, d in ALL.items():
    print("=" * 100)
    print(entry, d["name"])
    print("  size=%d n_insn=%d skip=%d last=%s atlas=%s" % (
        d["size"], d["n_insn"], d["n_skipdata"], d["last_insn"], d["atlas"]))
    print("  direct_callers:", d["direct_callers"][:20], ("...+%d" % (len(d["direct_callers"]) - 20)) if len(d["direct_callers"]) > 20 else "")
    print("  slots (%d):" % len(d["slots"]))
    for s in d["slots"]:
        if s.get("rtti"):
            print("     slot_va=%s vt=%s slot_off=%s slot_no=%s rtti=%s" % (
                s["slot_va"], s["vtable_base"], s.get("slot_off"), s.get("slot_no"), s["rtti_name"]))
        else:
            print("     slot_va=%s sec=%s (no RTTI)" % (s["slot_va"], s["section"]))
    ca = d["chA"]
    print("  chA P1=%d P2=%d P3=%d sites=%d" % (ca["p1"], ca["p2"], ca["p3"], len(ca["sites"])))
    for st in ca["sites"]:
        print("     call@%08X callee=%s test@%s %s jcc@%s %s | call_site_falsy=%s consts=%s" % (
            st["call_addr"], ("%08X" % st["callee"]) if st["callee"] else "?",
            st["test_addr"], st["test_kind"], st["jcc_addr"], st["jcc_mnemonic"],
            st["call_site_falsy"], st["callee_profile"]["falsifiable_consts"]))
    print("  chB tables=%d" % len(d["chB"]))

print("\nWROTE dump.json")
