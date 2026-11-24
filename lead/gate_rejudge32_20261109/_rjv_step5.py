# -*- coding: utf-8 -*-
"""_rjv_step5.py — 独立核验 §4(b)「补语境类后真剩 4 域」与 §5(b) 片段是否自洽。"""
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_rejudge32_20261109"
BASE = json.loads((ROOT / "lead" / "gate_doc_name_fix_20261109" / "_dn_regate_out.json").read_text(encoding="utf-8"))
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
spec = importlib.util.spec_from_file_location("_rjv_g7d", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

STRUCT = re.compile(r'^\s*(#{1,6}\s|\||\d+[\.、]\s)|<[^>\n]{1,40}>|是否已填|→|\b或\b')

def line_of(t, pos):
    s = t.rfind('\n', 0, pos) + 1
    e = t.find('\n', pos); e = len(t) if e < 0 else e
    return t[s:e]

rows = []
for row in BASE["rows"]:
    if not row.get("gateProblems"):
        continue
    dom = row["domain"]
    p = ROOT / dom.rstrip("/") / row["main"]
    t = p.read_text(encoding="utf-8", errors="replace")
    probs = []
    for prob in row["gateProblems"]:
        if prob.startswith("缺小节 "):
            if prob[5:] not in t:
                probs.append(prob)
        elif prob.startswith("缺要素 "):
            tok = prob[5:]
            ok, _ = g7.r9_element_present(t, tok)
            if not ok:
                probs.append(prob)
    banned = row.get("params", {}).get("banned", [])
    if banned:
        p10, w10, h10 = g7.r10_scan(t, banned)
        p12, _ = g7.r12_scan(t, banned)
        kept = [h for h in h10 if h["kind"] == "assertion" and not STRUCT.search(line_of(t, h["pos"]))]
        probs += ["R10:" + h["token"] + "@L" + str(t.count('\n', 0, h['pos']) + 1) for h in kept]
        probs += ["R12:" + x for x in p12]
    p11, _, _ = g7.r11_scan(t, p.parent, root=ROOT)
    probs += ["R11:" + x for x in p11]
    rows.append({"domain": dom, "naive_problems": row["gateProblems"],
                 "predicatized_problems": probs, "fail": bool(probs)})

plain_fail = [r["domain"] for r in rows if r["fail"]]
# 与 step4 无 STRUCT 的 7 域对照
out = {
    "domains_checked": len(rows),
    "fail_after_supplied_STRUCT_count": len(plain_fail),
    "fail_after_supplied_STRUCT_domains": plain_fail,
    "claimed_remaining_domains": ["matrix_ab_ruling_20261109", "matrix_reach_20261109",
                                 "n11_wording_fix_20261108", "s604_script_gap_20261109"],
    "s604_script_hunt_still_fails": "s604_script_hunt_20261109" in " ".join(plain_fail),
    "s604_script_hunt_L143_STRUCT_match": bool(STRUCT.search(
        (ROOT / "lead/s604_script_hunt_20261109/S604_SCRIPT_HUNT.md").read_text(encoding="utf-8", errors="replace").split("\n")[142])),
    "or_b_tests": [
        {"text": s, "match": bool(re.search(r"\b或\b", s))}
        for s in ["见证已填 或 S1 有记载", "见证已填或S1有记载", "通过档或存疑档", "A 或 B"]],
    "rows": rows,
}
(WD / "_rjv_step5_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
print("--- fail rows ---")
for r in rows:
    if r["fail"]:
        print(r["domain"], r["predicatized_problems"])
