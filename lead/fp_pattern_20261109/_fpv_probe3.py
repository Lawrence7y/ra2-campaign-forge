# -*- coding: utf-8 -*-
r"""_fpv_probe3.py — 独立复核员：核两处 numeric 表述（H5 字面支计数 / 表宽-fp 权衡曲线）
   及 d3 口径。只读复算；唯一写域 lead/fp_pattern_20261109/，前缀 _fpv_。"""
import sys, json, re, ast, types
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_pattern_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
AI = ROOT / "lead" / "advset_indep_20261109"
OUT = {}
def emit(k, v):
    OUT[k] = v
    print("[%s] %s" % (k, json.dumps(v, ensure_ascii=False)))

h5src = H5P.read_text(encoding="utf-8")
t = ast.parse(h5src)
A = {}
for n in t.body:
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
        try: A[n.targets[0].id] = ast.literal_eval(n.value)
        except Exception: pass
R12 = A["H5_R12_TEN"]; EX = A["H5_DN_EXTRA"]
r12_forms = R12.split("|")
ex_forms = EX.split("|")
# 通配支：包含 [^ 或 (?: 的那一整支（正则里是相邻三段字符串拼接为 1 个选择支）
# H5_DN_EXTRA 是 3 个 r"" 字符串隐式拼接；含 [^ 的那一支跨了拼接边界，
# 因此按 '|' 朴素切会把 1 条通配支切成 9 个碎片。
literal_branches_r12 = [x for x in r12_forms if x and "[^" not in x and "(?:" not in x]
ex_literal = [x for x in ex_forms if x and "[^" not in x and "(?:" not in x and ")" not in x]
# 更严谨：EX 里前 19 项是纯字面，第 20 项是通配支（含非捕获组）
ex_first19 = ex_forms[:19]
ex_wildcard = ex_forms[19:]
naive = [b for b in (R12 + "|" + EX).split("|") if b and "[^" not in b]
emit("h5_branch_count_audit", {
  "R12_TEN_n": len(r12_forms),
  "DN_EXTRA_naive_split_n": len(ex_forms),
  "DN_EXTRA_pure_literal_n": len(ex_first19),
  "DN_EXTRA_wildcard_fragments": ex_wildcard,
  "true_total_branches (10+19+1)": len(r12_forms) + len(ex_first19) + 1,
  "true_pure_literal_branches (10+19)": len(r12_forms) + len(ex_first19),
  "naive_split_minus_1_frag (fp_classify:108)": len(naive),
  "claimed_in_fp_classify_stdout_36": 37,
  "DG_ADVERSARIAL_245_says": "H5 = H5_DN_EXTRA 20 支(19 纯字面 + 1 带通配) + H5_R12_TEN 10 支 = 30 支",
  "verdict": "37 是朴素按 | 切后减去 1 个含[^碎片得到的数，含 8 个非独立碎片"
             "（认定/认为/承认/说/写/登/记/填)）；真正的纯字面支 = 29，总选择支 = 30。"
             "被核回件 _fp_classify_stdout.txt:36『H5 纯字面支数(不含通配) = 37』与"
             "DG_ADVERSARIAL.md:245 自述的 30/19 支冲突，属计数口径错误。"})

# 9 条 fp 命中串是否落在【真正的 29 条纯字面支】内（不依赖有缺陷的 37 列表）
D = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
fp_hits = {c["id"]: c["hits"].get("H5_lit", "") for c in D["cases"]
           if c["id"] in D["scoring_strict"]["H5_lit"]["fp_ids"]}
true_literals = set(r12_forms) | set(ex_first19)
check = {k: any(b == h or b in h for b in true_literals) for k, h in fp_hits.items()}
emit("h5_9fp_vs_true_29_literals", {"fp_hits": fp_hits, "per_id": check,
     "all_true": all(check.values()), "n_true_literals": len(true_literals),
     "verdict": "结论『9/9 命中串来自手写字面支』在正确 29 支口径下仍成立；只是 37 这个数字不对。"})

# 表宽 vs fp/fn 是否单调（被核回件 §4(d) / failureTypes 称『同一条表越宽⇒fp↑fn↓权衡曲线』）
S = D["scoring_strict"]
curve = [{"detector": "R12", "table": 10, "fp": S["R12"]["fp"], "fn": S["R12"]["fn"]},
         {"detector": "H5_lit", "table": 30, "fp": S["H5_lit"]["fp"], "fn": S["H5_lit"]["fn"]},
         {"detector": "DG_pure", "table": 105492, "fp": S["DG_pure"]["fp"], "fn": S["DG_pure"]["fn"]}]
emit("table_width_vs_fp_fn", {"rows_sorted_by_width": curve,
     "fp_monotone_increasing": all(curve[i]["fp"] <= curve[i+1]["fp"] for i in range(2)),
     "fn_monotone_decreasing": all(curve[i]["fn"] >= curve[i+1]["fn"] for i in range(2)),
     "counterexample": "H5_lit 表(30 支) 窄于 DG_pure(105,492 串)，但 fp=9 > DG fp=7",
     "verdict": "fn 随表宽单调下降（17→14→11）成立；fp 随表宽单调上升不成立（2→9→7）。"
                "被核回件『同一条表越宽⇒fp↑fn↓权衡曲线』对 fp 是过度概括。"
                "不影响主结论（构造偏差/非因果），但『机会面积』的定量表述应弱化为"
                "『表更宽使 fn 下降；fp 另受护栏/引证屏蔽影响』。"})

# d3 口径：回件 what/§5a『41 条 CATCH⇔d3=True 零反例』
G = json.loads((AI / "_ai_grade_out.json").read_text(encoding="utf-8"))
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
pure_catch = {x["id"] for x in V["rows"] if x["verdicts"]["DG_pure"] == "CATCH"}
dropin_catch = {x["id"] for x in V["rows"] if x["verdicts"]["DG_dropin"] == "CATCH"}
d3p = {r["id"] for r in G["rows"] if r["d3_pure"]}
d3d = {r["id"] for r in G["rows"] if r["d3_dropin"]}
d3any = {r["id"] for r in G["rows"] if r["d3_pure"] or r["d3_dropin"]}
emit("d3_tautology_scope", {
  "n_pure_catch": len(pure_catch), "n_dropin_catch": len(dropin_catch),
  "n_d3_pure": len(d3p), "n_d3_dropin": len(d3d), "n_d3_any": len(d3any),
  "pure_catch_eq_d3p": pure_catch == d3p,
  "dropin_catch_eq_d3d": dropin_catch == d3d,
  "d3_any_eq_dropin_catch": d3any == dropin_catch,
  "d3_any_eq_pure_catch": d3any == pure_catch,
  "verdict": "d3 恒真对两个口径分别成立（DG_pure: 19⇔19；DG_dropin: 21⇔21）。"
             "回件 what/§5a 写『41 条 CATCH⇔d3=True』未指明是哪个判定器，"
             "按 d3_any=21 与 DG_pure CATCH=19 不一致；_fp_recompute_stdout.txt:58 用的是 d3_pure"
             "（19⇔19）口径，是精确的。属表述不严谨，非数字错误。"})

(WD / "_fpv_probe3_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fpv_probe3_out.json")
