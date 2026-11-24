# -*- coding: utf-8 -*-
r"""_fp_classify.py — fp=7 / fn=11 逐条分类 + 三判定器失败类型对照（只读复算）。

不执行第二步(d) 的判别实验；不改任何对抗集/谓词/语料；唯一写域 lead/fp_pattern_20261109/。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fp_classify.py
"""
import sys, json, re
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_pattern_20261109"
AI = ROOT / "lead" / "advset_indep_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"

G = json.loads((AI / "_ai_grade_out.json").read_text(encoding="utf-8"))
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
D = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
R = json.loads((WD / "_fp_recompute_out.json").read_text(encoding="utf-8"))
byid = {r["id"]: r for r in G["rows"]}
verd = {x["id"]: x["verdicts"]["DG_pure"] for x in V["rows"]}
why = {c["id"]: c["why"] for c in D["cases"]}
attack = {c["id"]: c["attack"] for c in D["cases"]}
FP = R["DG_pure_strict"]["fp_ids"]
FN = R["DG_pure_strict"]["fn_ids"]

# ---- fp 7 逐条：失败类型 = 过宽(记忆/护栏污染)，细分护栏缺失类型 ----
FP_CAUSE = {
 "P06": ("未登记转折词「其实」", "DG_BREAK_RE 10 词(_dg_core.py:89) 未收；_scope 未切断；govern≤24 搭桥"),
 "P07": ("未登记追补词「说到底」", "同上"),
 "P08": ("未登记让步词「尽管」+ NEG2 完整谓语", "DG_BREAK_RE 未收 + NEG2 收「否认」(:63-67) 使 T12 零通配拼出"),
 "P09": ("第二主语「监理方」未登记 + guard 作用域", "_SECOND 14 词(:88) 未收；二次 veto 只查 hit_text(:182-184)"),
 "P10": ("并列词「或」在 hit_text 之外", "DG_COORD_RE(:91) 二次 veto 只查 hit_text(:182-184)，命中串不含「或」"),
 "P11": ("ASCII 双引号未登记", "DG_QUOTE_RE 4 类(:92) 未收；_mask_quotes(:148-158) 不生效"),
 "P12": ("书名号《》未登记", "同上"),
}
fn_cause = {
 "C01": ("覆盖不足", "MID「容」不在 23 项闭合表(:55-61)"),
 "C02": ("覆盖不足", "MID「许」未登记"),
 "C03": ("覆盖不足", "MID「想」未登记"),
 "C04": ("覆盖不足", "MID「想」未登记"),
 "C05": ("覆盖不足", "MID「准」未登记"),
 "C07": ("覆盖不足", "T3 comp{0,4}?(:118) 硬界：COMP=5 字越界"),
 "C08": ("抑制污染(veto 误杀)", "COMP 含「或」触发 DG_COORD_RE 二次 veto(:182-184)，真 DN 被当并列项"),
 "C09": ("覆盖不足", "comp 负向前瞻(:118) 排除 _SECOND「本件」，真 DN 被排除"),
 "C10": ("覆盖不足", "_SECOND 第二主语一刀切，未建模 ¬(本件¬宣告) 的命题管辖"),
 "C11": ("抑制污染(veto 误杀)", "「非不」在 PSEUDO_DN(:81-82) 被词首负向前瞻(:116) 否决"),
 "C12": ("抑制污染(veto 误杀)", "同上，「非不认可」"),
}

print("=== fp=7 逐条分类（DG_pure, strict） ===")
fp_out = []
for c in FP:
    r = byid[c]
    row = {"id": c, "expect": "PASS", "verdict": verd[c], "type": "误报 fp / 过宽(训练构式上)",
           "d1": r["d1"], "d3_pure": r["d3_pure"], "min_edit": r["min_edit"],
           "grade": r["grade"], "attack": attack[c], "hit": r["hit_pure"],
           "breach": FP_CAUSE[c][0], "src": FP_CAUSE[c][1], "why": why[c]}
    fp_out.append(row)
    print(json.dumps(row, ensure_ascii=False))

print("\n=== fn=11 逐条分类（DG_pure, strict） ===")
fn_out = []
for c in FN:
    r = byid[c]
    row = {"id": c, "expect": "CATCH", "verdict": verd[c], "type": fn_cause[c][0],
           "d1": r["d1"], "d3_pure": r["d3_pure"], "min_edit": r["min_edit"],
           "grade": r["grade"], "attack": attack[c], "src": fn_cause[c][1], "why": why[c]}
    fn_out.append(row)
    print(json.dumps(row, ensure_ascii=False))

print("\n=== 汇总 ===")
from collections import Counter
fp_type = Counter(x["type"] for x in fp_out)
fn_type = Counter(x["type"] for x in fn_out)
summary = {"fp_n": len(FP), "fn_n": len(FN),
           "fp_all_d1_nonempty": all(x["d1"] for x in fp_out),
           "fp_all_d3_true": all(x["d3_pure"] for x in fp_out),
           "fn_d1_empty": sum(1 for x in fn_out if not x["d1"]),
           "fn_d1_nonempty": sum(1 for x in fn_out if x["d1"]),
           "fn_d1_nonempty_ids": [x["id"] for x in fn_out if x["d1"]],
           "fn_types": dict(fn_type), "fp_types": dict(fp_type),
           "symmetry": "fp 全在 d1 非空(7/7)；fn 多数在 d1 空(9/11)，2 条 d1 非空却是 veto 误杀"}
print(json.dumps(summary, ensure_ascii=False))

# ---- 三判定器对照 ----
print("\n=== 三判定器失败类型对照 (strict, n=36) ===")
comp = {}
for key in ("DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"):
    s = D["scoring_strict"][key]
    fp_ids, fn_ids = s["fp_ids"], s["fn_ids"]
    comp[key] = {"fp": s["fp"], "fn": s["fn"],
                 "fp_all_d1_nonempty": all(byid[c]["d1"] for c in fp_ids),
                 "fp_d1_empty_ids": [c for c in fp_ids if not byid[c]["d1"]],
                 "fn_all_d1_empty": all(not byid[c]["d1"] for c in fn_ids),
                 "fn_d1_nonempty_ids": [c for c in fn_ids if byid[c]["d1"]],
                 "fp_ids": fp_ids, "fn_ids": fn_ids}
    print(json.dumps({key: comp[key]}, ensure_ascii=False))

# H5_lit fp 命中串是否都来自其手写词表（实读 H5_DN_EXTRA 字面支）
import ast
h5src = (ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py").read_text(encoding="utf-8")
t = ast.parse(h5src)
h5_lit = {}
for n in t.body:
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
        try: h5_lit[n.targets[0].id] = ast.literal_eval(n.value)
        except Exception: pass
branches = [b for b in (h5_lit["H5_R12_TEN"] + "|" + h5_lit["H5_DN_EXTRA"]).split("|") if b and "[^" not in b]
h5_hits = {c["id"]: c["hits"].get("H5_lit", "") for c in D["cases"]}
h5_branches_hit = {c: h5_hits[c] for c in D["scoring_strict"]["H5_lit"]["fp_ids"]}
print("\n=== H5_lit 9 条 fp 的命中串 ===")
print(json.dumps(h5_branches_hit, ensure_ascii=False))
print("H5 纯字面支数(不含通配) =", len(branches))
print("9/9 命中串为 H5 手写表内构式 =",
      all(any(b == h or b in h for b in branches) for h in h5_branches_hit.values()))

OUT = {"fp7_classified": fp_out, "fn11_classified": fn_out, "summary": summary,
       "detector_comparison_strict": comp,
       "h5_lit_fp_hits": h5_branches_hit,
       "h5_lit_branches_n": len(branches),
       "h5_lit_fp_all_from_literal_table": all(any(b == h or b in h for b in branches) for h in h5_branches_hit.values())}
(WD / "_fp_classify_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fp_classify_out.json")
