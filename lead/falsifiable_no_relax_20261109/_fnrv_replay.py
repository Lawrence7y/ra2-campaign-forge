# -*- coding: utf-8 -*-
"""Independent reviewer replay of _r9s_regress.py:204-206 / :223-229.

I re-derive the old formula myself from the source (not from _fnr_replay.py),
using the recorded per-element R9/R9S results in _r9s_regress_out.json.
Three NEW semantically-empty payloads (authored here, not copied) are pushed
through the actual R9S predicate, and I substitute the resulting flip tuples.

KEY: the old no_relaxation formula consumes ONLY (domain, token, whitelisted, main)
-- see _r9s_regress.py:183-185. Semantic detail _d is discarded at :179.
So ANY text change that preserves the same 5 flip keys cannot change the verdict.
"""
import hashlib
import json
import sys

ROOT = "D:/Project/ra2-campaign-forge/"
REF = ROOT + "lead/gate_r9sem_20261109/_r9s_regress_out.json"
OUT = ROOT + "lead/falsifiable_no_relax_20261109/_fnrv_replay_out.json"
sys.path.insert(0, ROOT + "lead/gate_r9sem_20261109")
import _r9s_predicates as R9S

# Three NOVEL semantic-empty payloads written by the reviewer. Each is
# form-like (contains the surface roles) but delivers NO semantic value.
# Target tokens picked to cover 3 distinct specs (S1, S3, S5).
MY_EMPTY = [
    ("RV-E1", "lead/matrix_ab_ruling_20261109/", "需谁批准",
     "## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准，本件不重录。\n"),
    ("RV-E2", "lead/n11_wording_fix_20261108/", "改前改后",
     "## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A\n- 【改前】旧句共 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】新句见方案 B 的对应行，本件不重录。\n- 【要点】逐处对照表另附。\n"),
    ("RV-E3", "lead/s604_script_gap_20261109/", "可重建",
     "## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n判定：正确算法【可唯一重建】。已有四重独立实现逐位一致，max|Δ|=0.000000；原始采样记录见归档索引，本件不重录。\n"),
]

ref = json.loads(open(REF, encoding="utf-8").read())
WL = {tuple(x) for x in ref["domains32"]["whitelist"]}
REF_FLIPS = [(f["domain"], f["token"]) for f in ref["domains32"]["flips"]]

print("=== INDEPENDENT: 3 novel semantic-empty payloads through the REAL R9S predicate ===")
emp_rows = []
for cid, dom, tok, txt in MY_EMPTY:
    ok0, lay0 = R9S.R9.r9_element_present(txt, tok)
    ok1, lay1, detail = R9S.r9s_element_present(txt, tok)
    # R9 must be absent and R9S present => a FLIP, otherwise no substitution possible
    is_flip = (not ok0) and ok1
    emp_rows.append({"id": cid, "domain": dom, "token": tok, "r9": ok0,
                     "r9s": ok1, "layer": lay1, "is_flip": is_flip,
                     "detail": detail})
    print("  %-6s %-14s r9=%-5s r9s=%-5s layer=%-9s FLIP=%s" %
          (cid, tok, ok0, ok1, lay1 or "(none)", is_flip))
    print("     text = " + repr(txt[:100]))

# Re-derive old formula from source :204-206 and :223-229.
# flips here are the recorded flip tuples; the old formula sees ONLY these keys.
def old_formula(flips, wl, samples_all_pass, four_ok=True):
    no_relax = (len([f for f in flips if not f["whitelisted"]]) == 0
                and len(flips) == len(wl)
                and all(f["whitelisted"] for f in flips))
    verdict = "PASS" if (samples_all_pass and no_relax and four_ok) else "FAIL"
    return no_relax, verdict

recorded_flips = [{"domain": d, "token": t, "whitelisted": (d, t) in WL}
                  for d, t in REF_FLIPS]
sa = ref["samples"]["all_pass"]
nr, vd = old_formula(recorded_flips, WL, sa)
print("\n=== INDEPENDENT re-derivation of old formula on recorded state ===")
print("  no_relaxation=%s  VERDICT=%s  n_flips=%d  n_wl=%d" % (nr, vd, len(recorded_flips), len(WL)))

# Now inject: all 3 of my empty texts ARE flips (checked above). The flip KEY
# multiset is unchanged, because each (domain,token) was already a recorded flip.
# Simulate "all 3 of my chosen conclusions are WRONG" by keeping the same keys.
my_keys = {(d, t) for _, d, t, _ in MY_EMPTY}
assert my_keys.issubset(set(REF_FLIPS)), "my tokens must be within existing flip set"
n_wrong = len(my_keys)

# old check has NO input for semantics, so its answer is literally identical.
nr_wrong, vd_wrong = old_formula(recorded_flips, WL, sa)
print("\n=== INDEPENDENT: old check on 'my 3 conclusions ALL WRONG' world ===")
print("  n_wrong_conclusions = %d" % n_wrong)
print("  flip keys after substitution = %s (UNCHANGED)" % sorted(REF_FLIPS))
print("  old no_relaxation=%s  old VERDICT=%s" % (nr_wrong, vd_wrong))
print("  => old check ALARMS? %s" % ("NO -- decorative" if vd_wrong == "PASS" else "yes"))

# Extra: semantic-empty payloads must be judged PRESENT by R9S to be usable as
# a valid counterexample (a genuine false-positive). Report which are.
usable = [r["id"] for r in emp_rows if r["is_flip"]]
print("\n  usable (R9=False,R9S=True) empty payloads = %s  (%d/3)" % (usable, len(usable)))

# Also verify the converse from source: old check FAILs on truth-preserving
# cardinality changes, proving it is blind to truth and allergic to counts.
print("\n=== INDEPENDENT: old check on truth-PRESERVING cardinality perturbations ===")
perturb = []
f2 = recorded_flips + [{"domain": "lead/handoff_pack_20261109/", "token": "需谁批准",
                        "whitelisted": False}]
a, b = old_formula(f2, WL, sa)
perturb.append({"case": "add_6th_true_flip", "truth": "all 5 original semantics intact",
                "no_relaxation": a, "VERDICT": b})
f3 = [f for f in recorded_flips if f["token"] != "需谁批准"]
a, b = old_formula(f3, WL, sa)
perturb.append({"case": "one_flip_made_literally_present", "truth": "semantics improved",
                "no_relaxation": a, "VERDICT": b})
wl4 = set(WL) - {("lead/matrix_ab_ruling_20261109/", "需谁批准")}
f4 = [{"domain": d, "token": t, "whitelisted": (d, t) in wl4} for d, t in REF_FLIPS]
a, b = old_formula(f4, wl4, sa)
perturb.append({"case": "drop_1_whitelist_pair", "truth": "all 5 semantics intact",
                "no_relaxation": a, "VERDICT": b})
for p in perturb:
    print("  %-34s no_relaxation=%-5s VERDICT=%s" % (p["case"], p["no_relaxation"], p["VERDICT"]))

out = {"ref_sha256": hashlib.sha256(open(REF, "rb").read()).hexdigest(),
       "my_empty_payloads": emp_rows, "n_wrong": n_wrong,
       "old_on_my_all_wrong": {"no_relaxation": nr_wrong, "VERDICT": vd_wrong},
       "truth_preserving_perturbations": perturb,
       "source_lines": ["_r9s_regress.py:179 (_d discarded)", ":183-185 (flip record)",
                        ":204-206 (no_relaxation)", ":223-229 (VERDICT)"]}
open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
print("\nWROTE _fnrv_replay_out.json")
