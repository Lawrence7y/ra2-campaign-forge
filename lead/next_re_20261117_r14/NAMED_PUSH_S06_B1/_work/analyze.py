# -*- coding: utf-8 -*-
"""S14 B1 逐行四环初步取证：①入口 ②RTTI/虚表 ③b② 站点 ④direct caller + 活虚表安装点。
输出 _work/analysis.json（每行一份 dict），不做裁定，只出事实。
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))

def entry_info(entry):
    ea = int(entry, 16)
    size = R.ATLAS.get(entry, {}).get("size")
    info = {"entry": entry, "va": "0x%08X" % ea, "in_text": R.in_text(ea),
            "atlas_size": size}
    if not size:
        # 无 atlas 边界：用下一条 atlas entry 推断
        nxt = min((int(k, 16) for k in R.ATLAS if int(k, 16) > ea), default=None)
        size = (nxt - ea) if nxt else None
        info["atlas_size"] = None
        info["fallback_size"] = size
    if not size:
        return info, []
    insns = R.disasm(ea, R.read_va(ea, size))
    info["n_disasm"] = len(insns)
    info["n_skipdata"] = sum(1 for i in insns if i.id == 0)
    info["first"] = insns[0].mnemonic + " " + insns[0].op_str if insns else None
    info["last"] = ("%s %s" % (insns[-1].mnemonic, insns[-1].op_str)) if insns else None
    info["ends_with_ret_or_jmp"] = bool(insns) and insns[-1].mnemonic.startswith(("ret", "jmp"))
    return info, insns

def main():
    out = []
    for i, r in enumerate(ROWS, 1):
        entry = r["entry"]
        ei, insns = entry_info(entry)
        rec = {"idx": i, "entry": entry, "name": r["name"], "grade": r["grade"], "ring1": ei}
        # ③b②
        if insns:
            chA = R.channel_screen_A(insns)
            rec["chA"] = {"p1": chA["p1"], "p2": chA["p2"], "p3": chA["p3"],
                          "sites": chA["sites"]}
            rec["chB"] = [{"jmp": "%08X" % t["jmp_addr"], "bound": t["bound"],
                           "ncase": t["ncase"], "n_targets": len(t["targets"])}
                          for t in R.channel_screen_B(insns)]
        # ②④
        w = C2.witness_entry(entry)
        rec["ring2_slots"] = w["slots"]
        rec["ring4_direct"] = w["direct_callers"]
        out.append(rec)
        print("row %2d %s %-28s ①insn=%s skip=%s ③A p1/p2/p3=%s ②slots=%d ④direct=%d" % (
            i, entry, r["name"],
            ei.get("n_disasm"), ei.get("n_skipdata"),
            (rec.get("chA", {}).get("p1"), rec.get("chA", {}).get("p2"), rec.get("chA", {}).get("p3")),
            len([s for s in w["slots"] if s.get("rtti_name")]), len(w["direct_callers"])))
    json.dump(out, open(os.path.join(WORK, "analysis.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("-> analysis.json")

if __name__ == "__main__":
    main()
