# -*- coding: utf-8 -*-
"""S13 B1 witness driver: 对每个候选跑 core2.witness_entry，输出 refs.json / witness.txt。
② = vtable 槽 (vt[slot]==entry) + RTTI COL→TD→name
④ = 该 vt 的 .text 构造安装点 (find_vtable_writes)，标 in_func / atexit / in_self
并列出 direct callers。
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core2 as C2
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))

out = {}
for r in ROWS:
    e = r["entry"]
    w = C2.witness_entry(e)
    out[e] = {"name": r["name"], "size": R.ATLAS.get(e, {}).get("size"), **w}

json.dump(out, open(os.path.join(WORK, "refs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lines = []
for e, v in out.items():
    lines.append("### %s %s size=%s" % (e, v["name"], v["size"]))
    lines.append("  direct_callers(%d): %s" % (len(v["direct_callers"]), ", ".join(v["direct_callers"])))
    for s in v["slots"]:
        lines.append("  slot@%s [%s] rtti=%s" % (
            s["slot_va"], s["section"], s.get("rtti_name") if s.get("rtti_name") else "NONE"))
        if s.get("vtable_base"):
            lines.append("     vt=%s slot_off=%s(#%d) col=%s td=%s name_va=%s name=%s" % (
                s["vtable_base"], s["slot_off"], int(s["slot_off"])//4,
                s["col"], s["td"], s["name_va"], s["rtti_name"]))
            for g in s.get("global_writes", []):
                f = g.get("in_func")
                lines.append("     install global@%s global=%s in_func=%s atexit=%s" % (
                    g["write_va"], g.get("global"),
                    (f[1], f[2]) if f else None, g.get("atexit")))
            if s.get("imm_loads"):
                lines.append("     imm_loads=%s" % ", ".join(s["imm_loads"]))
    lines.append("")

txt = "\n".join(lines)
open(os.path.join(WORK, "witness.txt"), "w", encoding="utf-8").write(txt)
print(txt)
