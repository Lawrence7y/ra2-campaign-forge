import json, os, pathlib, re, collections
BASE = r"D:\Project\ra2-campaign-forge"
WD = os.path.join(BASE, "lead", "eqdecl_gate_20261109")

# ---- 1. detector M-family count (code truth) ----
import importlib.util
spec = importlib.util.spec_from_file_location("_eq_detector", os.path.join(WD, "_eq_detector.py"))
eq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eq)
groups = {"M1": eq.M1, "M2": eq.M2, "M3": eq.M3, "M4": eq.M4, "M5": eq.M5}
for g, d in groups.items():
    print(g, "n_sub =", len(d), "keys =", ",".join(d.keys()))
print("ALL_M_total =", len(eq.ALL_M))
print("E_EQ_STRICT_n =", len(eq.E_EQ_STRICT), "Q1_LABEL_n =", len(eq.Q1_LABEL),
      "Q2_n =", len(eq.Q2), "SCOPE_n =", len(eq.SCOPE), "INTENSITY_n =", len(eq.INTENSITY),
      "UNIVERSAL_n =", len(eq.UNIVERSAL_CLAIM))
print("M2d_patterns =", eq.M2["M2d_不是近似"])
probe = "根因不是「R12 数值接近 1 所以近似省一层」，而是"
print("M2d_hits_MC104_probe =", eq._hits(probe, eq.M2["M2d_不是近似"]))

# ---- 2. full_out recompute ----
full = json.load(open(os.path.join(WD, "_eq_full_out.json"), encoding="utf-8"))
print("\n== scope ==")
print("read_dirs =", full["scope"]["read_dirs"])
print("n_md_files =", full["scope"]["n_md_files"])
for f in full["scope"]["md_files"]:
    print("  ", f)
print("listed_n_lines =", full["scope"]["listed_n_lines"])
print("\n== totals ==")
print(json.dumps(full["totals"], ensure_ascii=False))
print("findings_by_type =", full["findings_by_type"])
print("\n== by_file findings ==")
for f, d in sorted(full["by_file"].items(), key=lambda x: -x[1]["n_findings"]):
    print(f"  {d['n_findings']:3d}  {f}  {d['findings_by_type']}  anchors={d['n_anchors']}")

# skip_by_reason totals
agg = collections.Counter()
for f, d in full["by_file"].items():
    for k, v in d["skip_by_reason"].items():
        agg[k] += v
print("skip_by_reason_aggregate =", dict(agg))

# ---- 3. 45-row reconciliation ----
rows = full["listed_45_lines"]["rows"]
print("\n== listed_45_lines ==")
print("n_rows =", full["listed_45_lines"]["n_rows"], "n_anchored =", full["listed_45_lines"]["n_anchored"],
      "n_findings =", full["listed_45_lines"]["n_findings"])
vc = collections.Counter(x["verdict"] for x in rows)
print("verdict_counter =", dict(vc))
for x in rows:
    if x["verdict"] == "FAIL":
        print("  FAIL", x["file:line"], x["failure_type"])

# ---- 4. sampling recompute ----
s = full["sampling"]
print("\n== sampling ==")
print("n_samples =", s["n_samples"], "true =", s["n_true_positive_sample"], "false =", s["n_false_positive_sample"])
print("precision_estimate =", full["precision_recall_estimate"]["precision_estimate_from_sample"],
      "IS_MEASUREMENT =", full["precision_recall_estimate"]["IS_MEASUREMENT"])
for x in s["samples"]:
    print(f"  [{x['human_sample_label']}] {x['file:line']} bucket={x['bucket']} -> {x['actual_verdict']}/{x['actual_failure_type']}")

# ---- 5. three_gates_out matrix ----
tg = json.load(open(os.path.join(WD, "_eq_three_gates_out.json"), encoding="utf-8"))
print("\n== three_gates ==")
print("n_cases =", tg["n_cases"], "n_passed =", tg["n_passed"], "n_failed =", tg["n_failed"])
for r in tg["matrix_rows"]:
    print(f"  {r['gate']} {r['case']} {r['file:line']} exp={r['expected']} act={r['actual']} passed={r['passed']}")

# ---- 6. selftest recompute check ----
st = json.load(open(os.path.join(WD, "_eq_selftest_out.json"), encoding="utf-8"))
print("\n== selftest file ==")
print("n_controls =", st["n_controls"], "n_passed =", st["n_passed"], "n_failed =", st["n_failed"])
for c in st["controls"]:
    print(f"  {c['id']} exp={c['expect_verdict']}/{c['expect_failure_type']} act={c['actual_verdict']}/{c['actual_failure_type']} passed={c['passed']}")

# ---- 7. ledger scan-scope check ----
print("\n== ledger scope check ==")
print("PENDING in md_files? ", any("PENDING_DECISIONS" in f for f in full["scope"]["md_files"]))
print("GOAL_THREE in md_files? ", any("GOAL_THREE_TARGETS" in f for f in full["scope"]["md_files"]))
for rel, word in (("lead/PENDING_DECISIONS.md", "恒等"), ("lead/GOAL_THREE_TARGETS_20261018.md", "恒等")):
    p = os.path.join(BASE, rel)
    txt = open(p, encoding="utf-8").read()
    n = len(re.findall(word, txt))
    print(f"count[{word}] in {rel} =", n)

# ---- 8. 决定性集合等式 grep across scanned files ----
print("\n== 决定性集合等式 grep ==")
hits = 0
f3 = 0
for f in full["scope"]["md_files"]:
    p = os.path.join(BASE, f)
    for i, line in enumerate(open(p, encoding="utf-8").read().split("\n"), 1):
        if "决定性集合等式" in line:
            hits += 1
            rec = next((x for x in (full["per_file_full"] and
                next(y for y in full["per_file_full"] if y["file"] == f)["findings"]) if x["line"] == i), None)
            ft = rec["failure_type"] if rec else None
            if ft == "F3":
                f3 += 1
            print(f"  {f}:{i} finding_ft={ft}")
print("total_lines_with_string =", hits, " of which F3 findings =", f3)
