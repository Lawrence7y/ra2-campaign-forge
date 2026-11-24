# -*- coding: utf-8 -*-
"""
_eqv_their_check.py — 复核员对实现员交付的内存复算（只读，不写任何文件）。
(a) 内存重算他们的三关 9 案例矩阵，与存盘 _eq_three_gates_out.json 逐格比对；
(b) 重点核 METRIC_CONVENTION_AUDIT.md:104（关二）实际 verdict/flags；
(c) 内存重算他们的 selftest 10 控，与存盘 _eq_selftest_out.json 比对；
(d) 从存盘 _eq_full_out.json 抽取关键行（LI:13/223/242/338/267/384、METRIC:21/126、
    TAUTOLOGY:356/366、KEFF:432/434/440、EI:294/302、_ma:77）的 verdict+flags+原因；
(e) 全库「决定性集合等式」逐行清单及他们的判定；台账两件是否在扫描范围内。
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")

spec = importlib.util.spec_from_file_location("_eq_detector_theirs", HERE / "_eq_detector.py")
eq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eq)

tg_stored = json.loads((HERE / "_eq_three_gates_out.json").read_text(encoding="utf-8"))
st_stored = json.loads((HERE / "_eq_selftest_out.json").read_text(encoding="utf-8"))
fl_stored = json.loads((HERE / "_eq_full_out.json").read_text(encoding="utf-8"))

print("=== (a) 三关 9 案例内存复算 vs 存盘 JSON 逐格比对 ===")
recs = {}
for rel in sorted({r["file:line"].rsplit(":", 1)[0] for r in tg_stored["matrix_rows"]}):
    recs[rel] = eq.scan_file(ROOT / rel)

mismatches = 0
for row in tg_stored["matrix_rows"]:
    rel, ln = row["file:line"].rsplit(":", 1)
    ln = int(ln)
    rec = recs[rel]
    hit = None
    for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
        hit = next((x for x in rec[bucket] if x["line"] == ln), None)
        if hit:
            break
    act = f"{hit['verdict']}/{hit['failure_type'] or '-'}/{hit['category']}" if hit else "NO_ANCHOR_RECORD"
    same = (act == row["actual"]) and (row["passed"] is True)
    if not same:
        mismatches += 1
    print(f"  {row['case']} {row['file:line']} stored={row['actual']} passed={row['passed']} recomputed={act} match={same}")

print(f"  n_cases={tg_stored['n_cases']} stored n_passed={tg_stored['n_passed']} mismatched_cells={mismatches}")

print("\n=== (b) 关二重点 METRIC_CONVENTION_AUDIT.md:104 ===")
mc = recs["lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md"]
h104 = None
for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
    h104 = next((x for x in mc[bucket] if x["line"] == 104), None)
    if h104:
        break
print(json.dumps({"verdict": h104["verdict"], "failure_type": h104["failure_type"],
                  "category": h104["category"], "skip_reason": h104.get("skip_reason"),
                  "flags": h104["flags"]}, ensure_ascii=False, indent=1))

print("\n=== (c) selftest 10 控内存重算 vs 存盘 ===")
cs = eq.controls()
rep = [{"id": c["id"], "stored": f"{c['actual_verdict']}/{c['actual_failure_type']}",
        "recomputed": c["actual_verdict"], "passed": c["passed"]} for c in cs]
n_pass = sum(1 for c in cs if c["passed"])
same_ctrl = all(a["stored"] == a["recomputed"] for a in rep)
print(f"  recomputed n_passed={n_pass}/{len(cs)}; stored n_passed={st_stored['n_passed']}/{st_stored['n_controls']}; verdicts_match={same_ctrl}")
for a in rep:
    print(f"    {a['id']}: stored={a['stored']} recomputed={a['recomputed']} passed={a['passed']}")

print("\n=== (d) 存盘 full_out 关键行抽取（他们的 verdict + 旗标） ===")
want = [
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", [13, 52, 223, 242, 267, 338, 384]),
    ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", [21, 126]),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", [356, 366]),
    ("lead/keff_calc_20261109/KEFF_CALC.md", [432, 434, 440]),
    ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", [294, 302]),
]
per_file = {r["file"]: r for r in fl_stored["per_file_full"]}
# per_file_full 只有 findings 与 skips 前 20；findings 全量在里头吗？先看结构
allf = {r["file"]: r for r in fl_stored["per_file_full"]}
for rel, lns in want:
    d = allf.get(rel)
    if d is None:
        print(f"  {rel}: NOT IN full_out per_file_full")
        continue
    fmap = {x["line"]: x for x in d["findings"]}
    for ln in lns:
        x = fmap.get(ln)
        if x is None:
            print(f"  {rel}:{ln} -> 不是 finding（在 passes/skips/undec 里或未锚定）")
        else:
            fl = x["flags"]
            key = {k: fl[k] for k in ("I_raw", "I", "U_local", "O", "R", "R_same_line", "E", "E_eq", "T", "S", "B", "B_obs") if k in fl}
            print(f"  {rel}:{ln} -> {x['verdict']}/{x['failure_type']} flags={json.dumps(key, ensure_ascii=False)}")

print("\n=== (e) 全库「决定性集合等式」行 + 他们的判定 ===")
files15 = fl_stored["scope"]["md_files"]
print("  scope.md_files =", files15)
print("  两件台账在范围内? GOAL:", any("GOAL_THREE" in f for f in files15),
      " PENDING:", any("PENDING" in f for f in files15))
hits = []
for rel in files15:
    p = ROOT / rel
    lines = p.read_bytes().decode("utf-8", errors="replace").split("\n")
    for i, l in enumerate(lines, 1):
        if "决定性集合等式" in l:
            rec = allf.get(rel)
            v = "?"
            if rec:
                x = next((y for y in rec["findings"] if y["line"] == i), None)
                v = f"{x['verdict']}/{x['failure_type']}" if x else "not-a-finding"
            hits.append(f"{rel}:{i} their={v}")
for h in hits:
    print("  " + h)

print("\n=== (f) full_out 关键总数 vs 回件自报 ===")
t = fl_stored["totals"]
print("  totals:", json.dumps(t, ensure_ascii=False))
print("  findings_by_type:", json.dumps(fl_stored["findings_by_type"], ensure_ascii=False))
print("  listed_45: n_rows", fl_stored["listed_45_lines"]["n_rows"],
      "n_anchored", fl_stored["listed_45_lines"]["n_anchored"],
      "n_not_anchored", fl_stored["listed_45_lines"]["n_not_anchored"],
      "n_findings", fl_stored["listed_45_lines"]["n_findings"])
vc = {}
for r in fl_stored["listed_45_lines"]["rows"]:
    vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
print("  listed_45 verdict 分布:", json.dumps(vc, ensure_ascii=False))
for r in fl_stored["listed_45_lines"]["rows"]:
    if r["verdict"] == "FAIL":
        print(f"    FAIL: {r['file:line']} {r['failure_type']}")
s = fl_stored["sampling"]
print("  sampling: n", s["n_samples"], "true", s["n_true_positive_sample"],
      "false", s["n_false_positive_sample"])
print("  precision:", json.dumps(fl_stored["precision_recall_estimate"], ensure_ascii=False)[:400])

print("\n=== (g) skip_by_reason 全量合计 ===")
agg = {}
for f, d in fl_stored["by_file"].items():
    for k, v in d["skip_by_reason"].items():
        agg[k] = agg.get(k, 0) + v
print(" ", json.dumps(agg, ensure_ascii=False), "sum=", sum(agg.values()))
