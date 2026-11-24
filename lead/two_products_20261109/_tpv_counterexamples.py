# -*- coding: utf-8 -*-
"""_tpv_counterexamples.py — 独立构造「只改 A 不改 B」场景，套用交付门禁 _tp_crosscheck.py 的真实 CLI/rc。
不改任何只读件；所有变体写到本写域 _tpv_*.json，B 始终用原件。
"""
import copy, json, subprocess, sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "two_products_20261109"
R11 = REPO / "lead" / "r11_f2_fix_20261109"
GATE = W / "_tp_crosscheck.py"
A0 = json.loads((R11 / "_f2_compare_out.json").read_text(encoding="utf-8"))
B_ORIG = R11 / "_f2v_run_out.json"
PY = sys.executable

def run_gate(a_path):
    cp = subprocess.run([PY, "-I", "-X", "utf8", str(GATE), str(a_path), str(B_ORIG)],
                        capture_output=True, text=True)
    out = cp.stdout
    lines = [l for l in out.splitlines() if any(t in l for t in
             ("canonical_from_A", "canonical_from_B", "canonical_equal", "violations", "RESULT", "  - "))]
    return cp.returncode, lines

def emit(name, doc):
    p = W / ("_tpv_%s.json" % name)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return p

print("========== 基线（A 原件 / B 原件）==========")
rc, lines = run_gate(R11 / "_f2_compare_out.json")
print("rc =", rc)
for l in lines: print(" ", l)

# 找一个有 plus.warnings 的件用于插入
idx_pluswarn = next(i for i, r in enumerate(A0["results"]) if r["plus"]["warnings"])
idx_origwarn = next(i for i, r in enumerate(A0["results"]) if r["orig"]["warnings"])
print("\nchosen idx_pluswarn =", idx_pluswarn, " idx_origwarn =", idx_origwarn)

# ---- 场景 X1: 只改 A 的计数维度 warnings（模拟 A 侧新增 warning 规则，A.totals 不变、B 全不动）----
A1 = copy.deepcopy(A0)
A1["results"][idx_pluswarn]["plus"]["warnings"] = list(A1["results"][idx_pluswarn]["plus"]["warnings"]) + ["_tpv_synthetic_new_warning_rule"]
p1 = emit("X1_A_only_plus_warnings", A1)
print("\n========== X1 只改 A.results[].plus.warnings（+1 条），B 不动 ==========")
print("A.totals 未动；A.results warnings 现值(该件) =", len(A1["results"][idx_pluswarn]["plus"]["warnings"]))
rc, lines = run_gate(p1)
print("rc =", rc)
for l in lines: print(" ", l)

# ---- 场景 X1b: 只改 A 的 orig.warnings（更贴近 _mm_project_out.txt:7 的 warnings 漂移）----
A1b = copy.deepcopy(A0)
A1b["results"][idx_origwarn]["orig"]["warnings"] = list(A1b["results"][idx_origwarn]["orig"]["warnings"]) + ["_tpv_w1", "_tpv_w2", "_tpv_w3"]
p1b = emit("X1b_A_only_orig_warnings", A1b)
print("\n========== X1b 只改 A.results[].orig.warnings（+3 条，模拟 11→14 类漂移），B 不动 ==========")
rc, lines = run_gate(p1b)
print("rc =", rc)
for l in lines: print(" ", l)

# ---- 场景 X2: 只改 A，且 A 内部自洽（真实「重跑 A 生产者」：插入 merged 行 + 同步更新 A.totals）----
A2 = copy.deepcopy(A0)
# 找一个有 plus.bindings 的件
ib = next(i for i, r in enumerate(A2["results"]) if r["plus"]["bindings"])
merged = {"declared": "_tpv_merged_decl", "path": None, "match": True,
          "tier": "SAMEDOC_LINK_EQ", "citation": ""}
A2["results"][ib]["plus"]["bindings"].append(merged)
# A 生产者重跑会同步重算 totals（仍按 9 维定义）：bindings 用 orig 不变，plus_match +1，warnings 也可能变
A2["totals"]["plus_match"] = A2["totals"]["plus_match"] + 1  # 使 A 自洽
p2 = emit("X2_A_merged_selfconsistent", A2)
print("\n========== X2 只改 A（插入 merged 行 + A.totals 同步自洽），B 不动 ==========")
print("A.totals.plus_match 已同步为", A2["totals"]["plus_match"], "（A 内部自洽）")
rc, lines = run_gate(p2)
print("rc =", rc)
for l in lines: print(" ", l)

# ---- 场景 X3: 控制组，只改 A.totals（撰写人 C10 反例1 的复刻）----
A3 = copy.deepcopy(A0)
A3["totals"]["plus_match"] = 18
A3["totals"]["plus_path"] = 17
p3 = emit("X3_A_only_totals", A3)
print("\n========== X3 控制组：只改 A.totals（C10 反例1 复刻），B 不动 ==========")
rc, lines = run_gate(p3)
print("rc =", rc)
for l in lines: print(" ", l)

# ---- 场景 X4: 只改 B 的 warnings（检验不对称性）----
B4 = copy.deepcopy(json.loads(B_ORIG.read_text(encoding="utf-8")))
ib4 = next(i for i, r in enumerate(B4["results"]) if r["orig_warnings"])
B4["results"][ib4]["orig_warnings"] = list(B4["results"][ib4]["orig_warnings"]) + ["_tpv_B_warning"]
p4 = W / "_tpv_X4_B_only_orig_warnings.json"
p4.write_text(json.dumps(B4, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n========== X4 只改 B.results[].orig_warnings（+1 条），A 用原件 ==========")
cp = subprocess.run([PY, "-I", "-X", "utf8", str(GATE), str(R11 / "_f2_compare_out.json"), str(p4)],
                    capture_output=True, text=True)
print("rc =", cp.returncode)
for l in cp.stdout.splitlines():
    if any(t in l for t in ("canonical_equal", "violations", "RESULT", "  - ")): print(" ", l)

# ---- 场景 X5: 只改 A 的非计数业务字段（verdict / other_predicates_fail），B 不动 ----
A5 = copy.deepcopy(A0)
A5["results"][0]["plus_overall"] = ("FAIL" if A5["results"][0]["plus_overall"] == "PASS" else "PASS")
A5["results"][0]["other_predicates_fail"] = not A5["results"][0]["other_predicates_fail"]
p5 = emit("X5_A_only_verdict_fields", A5)
print("\n========== X5 只改 A.results[].verdict/other_predicates_fail，B 不动 ==========")
rc, lines = run_gate(p5)
print("rc =", rc)
for l in lines: print(" ", l)

print("\n========== 汇总判定 ==========")
