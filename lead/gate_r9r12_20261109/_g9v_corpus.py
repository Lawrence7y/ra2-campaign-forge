# -*- coding: utf-8 -*-
# _g9v_corpus.py — 复核 ⑥ 挑选偏差：独立枚举 lead/ depth≤1、3000B<size<200KB 的 .md（撰写人清点口径），
# 全量跑同口径门禁，比对「前 30 件」与「其余」的误报/真违规分布，并检验 30 件是否构成某种自然序的前缀。
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from _g9_gate import check_deliverable, REPO_ROOT  # noqa: E402

DOCS_30 = [
    "lead/GOAL3T_CRITERIA_STATUS_20261021.md",
    "lead/GOAL3T_e4_VERIFY_20261026.md",
    "lead/PENDING_DECISIONS.md",
    "lead/a_dim_reduced_20261108/A_REDUCED_FORM.md",
    "lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md",
    "lead/a_residual_20261106/TASK.md",
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md",
    "lead/b2b_candidate_20261106/TASK.md",
    "lead/b2b_candidate_20261106/TESTS_REPORT.md",
    "lead/b2b_candidate_lf_20261107/N1_CLOSURE.md",
    "lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md",
    "lead/b2b_candidate_review2_20261106/TASK.md",
    "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
    "lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md",
    "lead/b2b_candidate_review_20261106/TASK.md",
    "lead/b2b_design_20261106/B2B_DESIGN.md",
    "lead/b2b_design_20261106/TASK.md",
    "lead/b2b_design_20261106/_draft_semantics.md",
    "lead/b2b_design_20261106/_hunks_frag.md",
    "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md",
    "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md",
    "lead/b2b_n1_binding_20261107/N1_BINDING.md",
    "lead/b2b_preaudit_20261106/B2B_PREAUDIT.md",
    "lead/b2b_preaudit_20261106/TASK.md",
    "lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md",
    "lead/b2_preaudit_20261106/B2_PREAUDIT.md",
    "lead/b2_preaudit_20261106/TASK.md",
    "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md",
    "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md",
    "lead/b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md",
]
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

lead = REPO_ROOT / "lead"
files = []
for p in lead.glob("*.md"):
    files.append(p)
for p in lead.glob("*/*.md"):
    files.append(p)
sel = [p for p in files if 3000 < p.stat().st_size < 200000]
sel_rel = sorted(str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in sel)
print("enumerated depth<=1 md total(without size filter):", len(files),
      "| in size range:", len(sel_rel))
s30 = set(DOCS_30)
sset = set(sel_rel)
print("DOCS_30 members found in enumeration: %d/30; extra: %s"
      % (len(s30 & sset), sorted(s30 - sset)))

# 序检验：DOCS_30 是否某自然序的前缀
lex = [r for r in sel_rel if r in s30 or True]  # lexicographic 全列
prefix_lex = [r for r in lex[:30]]
mtime = sorted((str(p.relative_to(REPO_ROOT)).replace("\\", "/"), p.stat().st_mtime)
               for p in sel)
prefix_mtime = [r for r, _ in mtime[:30]]
print("DOCS_30 == lexicographic first30:", DOCS_30 == prefix_lex)
print("DOCS_30 == mtime-asc first30:", DOCS_30 == prefix_mtime)

# 全量跑门禁（同口径）
results = {}
for rel in sel_rel:
    r = check_deliverable(REPO_ROOT / rel, REQ, FORB)
    results[rel] = r

def bucket(rel):
    return "FIRST30" if rel in s30 else "REST"

FIRST30_EMPTY = {"n": 0, "clean": 0, "r9miss": 0, "r11nobind": 0, "r11other": 0,
                 "r10_assert": 0, "r12": 0, "bind": 0, "bind_path": 0, "match_true": 0,
                 "haskobj": 0}
agg = {"FIRST30": dict(FIRST30_EMPTY), "REST": dict(FIRST30_EMPTY)}
rest_true_viol, rest_r11other = [], []
for rel, r in results.items():
    b = bucket(rel)
    a = agg[b]
    a["n"] += 1
    if not r["problems"]:
        a["clean"] += 1
    p11 = r["predicates"]["R11"]
    a["bind"] += p11["bindings"]
    a["bind_path"] += sum(1 for x in p11["binding_details"] if x.get("path"))
    a["match_true"] += p11["match_true"]
    for x in r["problems"]:
        m = x["msg"]
        if m.startswith("缺要素"):
            a["r9miss"] += 1
        elif m.startswith("缺 SHA256 绑定行"):
            a["r11nobind"] += 1
        elif m.startswith("引用锚"):
            a["r11other"] += 1
            if b == "REST":
                rest_r11other.append({"rel": rel, "msg": m[:120]})
        else:
            pass
    if r["predicates"]["R10"]["kinds"]["assertion"]:
        a["r10_assert"] += 1
        if b == "REST":
            rest_true_viol.append({"rel": rel, "kinds": r["predicates"]["R10"]["kinds"]})
    if r["predicates"]["R12"]["double_neg_hits"]:
        a["r12"] += 1
        if b == "REST":
            rest_true_viol.append({"rel": rel, "r12": r["predicates"]["R12"]["double_neg_hits"]})
    if "被核对象" in r["predicates"]["R9"].get("problems", []) or True:
        pass

# 「回件型」启发统计：含「被核对象」字样的件数（前30 vs 其余）
hask30 = sum(1 for rel in DOCS_30 if results[rel]["predicates"]["R11"]["bindings"] > 0
             or "被核对象" in (REPO_ROOT / rel).read_bytes().decode("utf-8", errors="replace"))
haskrest = sum(1 for rel, r in results.items()
               if bucket(rel) == "REST"
               and ("被核对象" in (REPO_ROOT / rel).read_bytes().decode("utf-8", errors="replace")))
agg["FIRST30"]["haskobj"] = hask30
agg["REST"]["haskobj"] = haskrest

print(json.dumps(agg, ensure_ascii=False, indent=1))
print("REST true-violation candidates:", json.dumps(rest_true_viol, ensure_ascii=False)[:2000])
print("REST r11-other (anchor) problems:", json.dumps(rest_r11other, ensure_ascii=False)[:2000])

(HERE / "_g9v_corpus_out.json").write_text(json.dumps({
    "n_enumerated": len(sel_rel), "d30_in_enum": len(s30 & sset),
    "prefix_lex": DOCS_30 == prefix_lex, "prefix_mtime": DOCS_30 == prefix_mtime,
    "agg": agg, "rest_true_viol": rest_true_viol, "rest_r11other": rest_r11other,
    "rest_clean": sorted(r for r in results if bucket(r) == "REST" and not results[r]["problems"]),
}, ensure_ascii=False, indent=1), encoding="utf-8")
