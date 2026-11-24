# -*- coding: utf-8 -*-
"""_tpv_counterexamples2.py — 构造 §4(a) 头号风险场景：「只给 A 加新维度」/「只给 B 加新维度」，
以及 A 侧补 warnings 到 totals。全部经 _tp_crosscheck.py 真实 CLI + rc 判定。
"""
import copy, json, subprocess, sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "two_products_20261109"
R11 = REPO / "lead" / "r11_f2_fix_20261109"
GATE = W / "_tp_crosscheck.py"
A0 = json.loads((R11 / "_f2_compare_out.json").read_text(encoding="utf-8"))
B0 = json.loads((R11 / "_f2v_run_out.json").read_text(encoding="utf-8"))
PY = sys.executable

def gate(a_doc, b_doc, tag):
    pa, pb = W / ("_tpv_%s_A.json" % tag), W / ("_tpv_%s_B.json" % tag)
    pa.write_text(json.dumps(a_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    pb.write_text(json.dumps(b_doc, ensure_ascii=False, indent=1), encoding="utf-8")
    cp = subprocess.run([PY, "-I", "-X", "utf8", str(GATE), str(pa), str(pb)],
                        capture_output=True, text=True)
    print("  rc =", cp.returncode)
    for l in cp.stdout.splitlines():
        if any(t in l for t in ("canonical_equal", "violations", "RESULT", "  - ")):
            print("   ", l)

print("=== Y1: 只给 A.totals 加一个新维度 merged_count=1（§4(a) 头号场景：只改一处新增维度），B 完全不动 ===")
A1 = copy.deepcopy(A0); A1["totals"]["merged_count"] = 1
print("  A.totals keys:", sorted(A1["totals"]))
gate(A1, B0, "Y1_A_new_dim")

print("\n=== Y2: 只给 B.totals 加一个新维度 merged_count=1，A 完全不动 ===")
B2 = copy.deepcopy(B0); B2["totals"]["merged_count"] = 1
print("  B.totals keys:", sorted(B2["totals"]))
gate(A0, B2, "Y2_B_new_dim")

print("\n=== Y3: A 侧把 warnings 两维补进 totals（合法 schema 升级，只改 A），B 不动 ===")
A3 = copy.deepcopy(A0); A3["totals"]["orig_warnings"] = 18; A3["totals"]["plus_warnings"] = 11
print("  A.totals keys:", sorted(A3["totals"]))
gate(A3, B0, "Y3_A_adds_warnings_to_totals")

print("\n=== Y4: 只改 A 的逐件业务判定字段 plus.verdict（只改一处），B 不动 ===")
A4 = copy.deepcopy(A0); A4["results"][0]["plus"]["verdict"] = "FORCED_FAIL"
gate(A4, B0, "Y4_A_only_verdict")

print("\n=== Y5: 同时改两份、且都写相同新 counting_policy 但 results 未含该维度（『两份一起漏改』探针）===")
A5 = copy.deepcopy(A0); B5 = copy.deepcopy(B0)
A5["counting_policy"] = B5["counting_policy"] = "deadbeef" * 8
A5["totals"]["merged_count"] = B5["totals"]["merged_count"] = 0
gate(A5, B5, "Y5_both_same_policy_no_TP7")

print("\n=== 结论提示 ===")
print("若 Y1/Y2/Y3/Y5 出现 rc=0 / RESULT=OK，则交付门禁对『只改一处新增维度』与『两份一起漏改』静默。")
