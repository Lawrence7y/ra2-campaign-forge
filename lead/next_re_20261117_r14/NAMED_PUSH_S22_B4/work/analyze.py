# -*- coding: utf-8 -*-
"""S22 B2 逐行四环初筛：①入口 ②RTTI/虚表 ③b②/③b① 站点 ④direct/install。只读目标。"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b4_rows.json"), encoding="utf-8") as f:
    B2 = json.load(f)["rows"]

def slotnum_from_name(name):
    m = re.search(r"::slot(\d+)$", name)
    return int(m.group(1)) if m else None

def analyze_one(row):
    ea = int(row["entry"], 16)
    name = row["name"]
    size = int(row["size"])
    out = {"entry": row["entry"], "name": name, "size": size}

    # ---- ring1: entry in text, atlas boundary, disasm coherence, tail ----
    insns = R.disasm_body(ea, size)
    code = R.read_va(ea, size)
    r1 = {
        "in_text": R.in_text(ea),
        "atlas_size": R.ATLAS.get(R.hx(ea), {}).get("size"),
        "n_insn": len([i for i in insns if i.id != 0]),
        "n_skipdata": len([i for i in insns if i.id == 0]),
        "last": (insns[-1].mnemonic + " " + insns[-1].op_str) if insns else None,
    }
    out["ring1"] = r1

    # ---- ring2: dword refs in non-text -> slot -> RTTI chain; check slot num ----
    wit = C.witness_entry(row["entry"])
    out["direct_callers"] = wit["direct_callers"]
    r2 = {"slotnum_clue": slotnum_from_name(name), "cands": []}
    for sl in wit["slots"]:
        cand = {
            "slot_va": sl["slot_va"], "section": sl["section"],
            "rtti_name": sl.get("rtti_name"),
            "vtable_base": sl.get("vtable_base"), "slot_off": sl.get("slot_off"),
            "col": sl.get("col"), "td": sl.get("td"), "name_va": sl.get("name_va"),
            "imm_loads": sl.get("imm_loads", []),
            "global_writes": sl.get("global_writes", []),
        }
        if sl.get("slot_off") is not None and r2["slotnum_clue"] is not None:
            cand["slotnum_actual"] = sl["slot_off"] // 4
            cand["slotnum_match"] = (sl["slot_off"] // 4 == r2["slotnum_clue"])
        else:
            cand["slotnum_actual"] = None
            cand["slotnum_match"] = None
        r2["cands"].append(cand)
    out["ring2"] = r2

    # ---- ring3b: channel A (call->test->jcc) + channel B (jump table) ----
    chA = R.channel_screen_A(insns)
    chB = R.channel_screen_B(insns)
    out["ring3b"] = {
        "channelA": {"p1": chA["p1"], "p2": chA["p2"], "p3": chA["p3"], "sites": chA["sites"]},
        "channelB": chB,
    }
    return out

def main():
    results = [analyze_one(r) for r in B2]
    with open(os.path.join(HERE, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    for r in results:
        r2 = r["ring2"]
        nailed = [c for c in r2["cands"] if c["rtti_name"] and c["slotnum_match"]]
        chA = r["ring3b"]["channelA"]
        chB = r["ring3b"]["channelB"]
        print("%s %-52s R1(last=%s skip=%d atlas=%s) R2(nail=%d/%d clue=%s) R3b(A p3=%d,B tbl=%d) R4(direct=%d)" % (
            r["entry"], r["name"][:52], r["ring1"]["last"], r["ring1"]["n_skipdata"], r["ring1"]["atlas_size"],
            len(nailed), len(r2["cands"]), r2["slotnum_clue"],
            chA["p3"], len(chB), len(r["direct_callers"])))
        for c in r2["cands"]:
            print("     slot=%s off=%s rtti=%s" % (c["slot_va"], c.get("slot_off"), c.get("rtti_name")))

if __name__ == "__main__":
    main()
