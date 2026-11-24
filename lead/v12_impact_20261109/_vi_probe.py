# -*- coding: utf-8 -*-
r"""_vi_probe.py -- S3 DEFAULT 可达性 / 回退风险 / 逐 S 级归因探针（只读，影子）。v3

跑法：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_vi_probe.py

v3 相对 v2 的修正（如实登记）：v2 用 importlib import 了一没有 __main__ guard 的
  回归脚本，import 时其 main() 连带实跑并打印，污染 stdout。v3 改用 ast.literal_eval
  从源码文本里只取词表常量，不执行任何被读模块；v1 曾误用自造词表，v2/v3 已弃用。

词表来源（AST 静态读取，零执行）：
  · lead/gate_n13_20261109/_n13_predicates.py:25  DEFAULT_TOKENS
  · lead/gate_fp7_20261108/_g7_reverse_validate.py:26  ASSERT_TOKENS
语料（全部库内既有件，非本任务构造）：
  · N13 回归 26 NEGATIVES（标注真断言，expect=CATCH）+ 16 POSITIVES（expect=PASS），
    逐字来自 lead/gate_n13_20261109/_n13_regression.py:46-113。
  · g7 真违规样件 TV2/TV3 逐行读盘，逐行给 ground truth：
    TV2 五处正面断言 CATCH；TV3 L8/L12 双重否定=肯定 CATCH、L10 单重否定控制行
    「应豁免」= PASS（_g7_tv3_double_negation.md:10 原文括注）。
  · 32 域现盘 26 命中（读 _vi_shadow_out.json 复核归因）。

逐处复算四级归因（S0 hard / S1 override / S2 weak / S3 default）——classify_v12
命中上级会提前 return，下级是否被同触必须外部独立算，否则审计不可追溯。
单列：S3 且本应 PASS（新误报）、V1 且本应 CATCH（回退）、V2 且本应 PASS（新增误报）。
另给【单元级】聚合：一个单元内任一 V2 => 整单元被抓（与真门禁的句级口径一致）。

零真机、零采样；只读，不插任何真门禁。
"""
import sys
sys.dont_write_bytecode = True
import ast
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "v12_impact_20261109"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
N13_REG = ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py"
N13_PRED_PY = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
G7_PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G7_RV = ROOT / "lead" / "gate_fp7_20261108" / "_g7_reverse_validate.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ast_const(path, varname):
    """只从源码 AST 取模块级常量，绝不执行该文件。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == varname:
                    return list(ast.literal_eval(node.value))
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == varname:
            return list(ast.literal_eval(node.value))
    raise KeyError("constant %r not found in %s" % (varname, path))


R = load(RULE, "_vi_probe_rule")
G7 = load(G7_PRED, "_vi_probe_g7")
N13 = load(N13_REG, "_vi_probe_n13")

N13_TOKENS = ast_const(N13_PRED_PY, "DEFAULT_TOKENS")
ASSERT_TOKENS = ast_const(G7_RV, "ASSERT_TOKENS")


def hits_of(text, toks):
    out = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            out.append((m.start(), tok))
    out.sort()
    return out


def stage_of(v, text, pos, end, tok):
    """外部独立复算四级标记是否同触（classify_v12 命中上级会提前 return）。"""
    line, U, off, is_table, rel_u = R._unit_and_line(text, pos, end, tok)
    pre, post = U[:max(0, rel_u)], U[max(0, rel_u) + len(tok):]
    U_bare = R._strip_quotes(U)
    adj_neg = bool(pre) and (pre[-1] in R.ADJ_NEG_CHARS or bool(R.ADJ_NEG_RE.search(pre)))
    prohibit_U = any(k in U_bare for k in R.PROHIBIT)
    ov_kw = [k for k in R.V2_OVERRIDE if k in U]
    ov_re = bool(R.V2_OVERRIDE_RE.search(U))
    weak = bool(R.W1_RE.search(pre)) or bool(R.W1_NUM_RE.match(U) or R.W1_NUM_RE.match(line))
    hard = bool(v["hard"])
    return {"S0_hard": hard,
            "S1_override_present": bool(ov_kw or ov_re),
            "S1_override_kw": ov_kw,
            "S1_would_fire": bool(ov_kw or ov_re) and not adj_neg and not prohibit_U,
            "S2_weak_present": weak,
            "S3_default": v["review_flag"],
            "taken": ("S0" if hard else ("S1" if v["override"] else
                      ("S2" if v["weak"] else ("S3" if v["review_flag"] else "?")))),
            "hard_AND_override": hard and bool(ov_kw or ov_re),
            "hard_AND_weak": hard and weak}


def main():
    lines = ["=== _vi_probe.py v3 S3 可达性 / 回退探针 ===",
             "N13_DEFAULT_TOKENS = %r (AST from %s:25)" % (N13_TOKENS, N13_PRED_PY.name),
             "ASSERT_TOKENS      = %r (AST from %s:26)" % (ASSERT_TOKENS, G7_RV.name)]
    recs = []

    corpus = []
    for sid, text, note, src in N13.NEGATIVES:
        corpus.append(("N13_NEG/" + sid, text, N13_TOKENS, "CATCH", src + " | " + note))
    for sid, text, expect, src in N13.POSITIVES:
        corpus.append(("N13_POS/" + sid, text, N13_TOKENS, "PASS", src))

    tv2 = ROOT / "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md"
    tv3 = ROOT / "lead/gate_fp7_20261108/_g7_tv3_double_negation.md"
    for lab, path in [("TV2", tv2), ("TV3", tv3)]:
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.split("\n"), 1):
            if not hits_of(line, ASSERT_TOKENS):
                continue
            if lab == "TV2":
                exp = "CATCH"   # _g7_reverse_validate.py:101 期望正面断言 R10 fail
            else:
                exp = "PASS" if i == 10 else "CATCH"
            note = "逐字读盘 %s L%d" % (path.as_posix(), i)
            if lab == "TV3" and i == 10:
                note += "（原文括注「单重否定，应豁免」）"
            corpus.append(("R10_TV/%s:L%d" % (lab, i), line, ASSERT_TOKENS, exp, note))

    lines.append("")
    lines.append("[A/B] 库内既有语料：N13 NEG %d + POS %d + TV2/TV3 命中行 => %d 单元" %
                 (len(N13.NEGATIVES), len(N13.POSITIVES), len(corpus)))
    stat = {"n_hits": 0, "V1": 0, "V2": 0, "S0": 0, "S1": 0, "S2": 0, "S3": 0,
            "s3_on_should_PASS": 0, "V1_on_should_CATCH": 0,
            "V2_on_should_PASS": 0, "V1_on_should_PASS": 0, "V2_on_should_CATCH": 0,
            "co_hard_override": 0, "co_hard_weak": 0}
    unit_rows = []
    for cid, text, toks, expect, note in corpus:
        hs = hits_of(text, toks)
        unit_verdicts = []
        for pos, tok in hs:
            v = R.classify_v12(text, pos, pos + len(tok), tok)
            st = stage_of(v, text, pos, pos + len(tok), tok)
            r10k = G7.r10_context(text, pos, pos + len(tok))["kind"]
            rec = {"corpus": cid, "expect": expect, "note": note, "tok": tok,
                   "pos": pos, "text": text[:220].replace("\n", "\\n"),
                   "r10_kind": r10k, "v12": v["verdict"], "hard": v["hard"],
                   "weak": v["weak"], "override": v["override"],
                   "review": v["review_flag"], "reason": v["reason"],
                   "unit": v["unit"], "stages": st}
            recs.append(rec)
            unit_verdicts.append(v["verdict"])
            stat["n_hits"] += 1
            stat["V1" if v["verdict"] == "V1" else "V2"] += 1
            stat[st["taken"]] = stat.get(st["taken"], 0) + 1
            if v["review_flag"]:
                stat["S3"] += 1
            if st["S3_default"] and expect == "PASS":
                stat["s3_on_should_PASS"] += 1
            if v["verdict"] == "V1" and expect == "CATCH":
                stat["V1_on_should_CATCH"] += 1
            if v["verdict"] == "V2" and expect == "PASS":
                stat["V2_on_should_PASS"] += 1
            if v["verdict"] == "V2" and expect == "CATCH":
                stat["V2_on_should_CATCH"] += 1
            if v["verdict"] == "V1" and expect == "PASS":
                stat["V1_on_should_PASS"] += 1
            if st["hard_AND_override"]:
                stat["co_hard_override"] += 1
            if st["hard_AND_weak"]:
                stat["co_hard_weak"] += 1
            lines.append("  %-16s expect=%-5s tok=%-8s R10=%-13s V12=%s taken=%s S3=%-5s hard=%r ov=%r weak=%r" %
                         (cid, expect, tok, r10k, v["verdict"], st["taken"],
                          v["review_flag"], v["hard"], v["override"], v["weak"]))
            lines.append("        TEXT = %s" % text[:220].replace("\n", "\\n"))
            lines.append("        UNIT = %r" % v["unit"])
        # 单元级：任一 V2 => 整单元被抓
        unit_catch = "V2" in unit_verdicts
        unit_rows.append({"cid": cid, "expect": expect, "n_hits": len(hs),
                          "per_hit": unit_verdicts, "unit_catches": unit_catch,
                          "correct": (unit_catch == (expect == "CATCH"))})
    no_hit = [(cid, expect) for cid, text, toks, expect, note in corpus if not hits_of(text, toks)]
    n_units_with_hits = len([u for u in unit_rows if u["n_hits"]])
    n_unit_correct = len([u for u in unit_rows if u["n_hits"] and u["correct"]])
    n_unit_fp = len([u for u in unit_rows if u["n_hits"] and u["expect"] == "PASS" and u["unit_catches"]])
    n_unit_fn = len([u for u in unit_rows if u["n_hits"] and u["expect"] == "CATCH" and not u["unit_catches"]])
    lines.append("  [单元级聚合] 有命中单元=%d 判对=%d 单元级误报(FP)=%d 单元级漏报(FN/回退)=%d" %
                 (n_units_with_hits, n_unit_correct, n_unit_fp, n_unit_fn))
    for u in unit_rows:
        if u["n_hits"] and not u["correct"]:
            lines.append("     MISMATCH %-16s expect=%-5s per_hit=%r catches=%s" %
                         (u["cid"], u["expect"], u["per_hit"], u["unit_catches"]))

    # ---------- C. 32 域现盘归因复核 ----------
    shadow = json.loads((WD / "_vi_shadow_out.json").read_text(encoding="utf-8"))
    dom_stat = {}
    for row in shadow["rows"]:
        for h in row["hits"]:
            d = row["domain"]
            b = dom_stat.setdefault(d, {"hits": 0, "V1": 0, "V2": 0, "S0": 0, "S1": 0,
                                        "S2": 0, "S3": 0, "hard_marks": [],
                                        "hard_and_override": 0, "hard_and_weak": 0})
            b["hits"] += 1
            b["V1" if h["v12_verdict"] == "V1" else "V2"] += 1
            b["hard_marks"].extend(h["hard"])
            if h["hard"]:
                b["S0"] += 1
            if h["override"]:
                b["S1"] += 1
            if h["weak"]:
                b["S2"] += 1
            if h["review_flag"]:
                b["S3"] += 1
            if h["co"]["hard_AND_override"]:
                b["hard_and_override"] += 1
            if h["co"]["hard_AND_weak"]:
                b["hard_and_weak"] += 1

    summary = {
        "token_sets": {"N13_DEFAULT_TOKENS": N13_TOKENS, "ASSERT_TOKENS": ASSERT_TOKENS},
        "corpus_units": len(corpus),
        "corpus_units_with_hits": n_units_with_hits,
        "corpus_hits": stat["n_hits"],
        "corpus_v12_verdict": {"V1": stat["V1"], "V2": stat["V2"]},
        "corpus_stage_taken": {k: stat[k] for k in ("S0", "S1", "S2", "S3")},
        "corpus_S3_default_hits": stat["S3"],
        "corpus_S3_on_should_PASS": stat["s3_on_should_PASS"],
        "corpus_V1_on_should_CATCH_regression_candidates": stat["V1_on_should_CATCH"],
        "corpus_V2_on_should_PASS_fp_candidates": stat["V2_on_should_PASS"],
        "corpus_V2_on_should_CATCH": stat["V2_on_should_CATCH"],
        "corpus_V1_on_should_PASS": stat["V1_on_should_PASS"],
        "corpus_co_hard_override": stat["co_hard_override"],
        "corpus_co_hard_weak": stat["co_hard_weak"],
        "corpus_no_literal_hit_units": len(no_hit),
        "corpus_unit_level": {"units_with_hits": n_units_with_hits,
                              "correct": n_unit_correct, "FP": n_unit_fp, "FN": n_unit_fn},
        "domains_32_stage_attribution": dom_stat,
        "domains_32_S3_total": sum(v["S3"] for v in dom_stat.values()),
        "domains_32_hard_and_override_total": sum(v["hard_and_override"] for v in dom_stat.values()),
        "domains_32_hard_and_weak_total": sum(v["hard_and_weak"] for v in dom_stat.values()),
    }
    lines.append("")
    lines.append("=== SUMMARY ===")
    lines.append(json.dumps(summary, ensure_ascii=False, indent=1))
    (WD / "_vi_probe_out.json").write_text(
        json.dumps({"summary": summary, "rows": recs, "unit_rows": unit_rows},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (WD / "_vi_probe_out.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("== _vi_probe.py v3 完成（AST 取词表，零副作用 import）==")
    print("N13_DEFAULT_TOKENS=%r ASSERT_TOKENS=%r" % (N13_TOKENS, ASSERT_TOKENS))
    print("库内语料单元=%d 有命中单元=%d 字面命中=%d" %
          (len(corpus), n_units_with_hits, stat["n_hits"]))
    print("V12 verdict: V1=%d V2=%d ; 归因 S0=%d S1=%d S2=%d S3=%d" %
          (stat["V1"], stat["V2"], stat["S0"], stat["S1"], stat["S2"], stat["S3"]))
    print("逐处：S3且应PASS=%d ; V1且应CATCH(回退)=%d ; V2且应PASS(新增误报)=%d ; V2且应CATCH=%d" %
          (stat["s3_on_should_PASS"], stat["V1_on_should_CATCH"],
           stat["V2_on_should_PASS"], stat["V2_on_should_CATCH"]))
    print("单元级：判对=%d/%d 单元FP=%d 单元FN=%d" %
          (n_unit_correct, n_units_with_hits, n_unit_fp, n_unit_fn))
    print("32 域现盘：S3=%d hard∧override=%d hard∧weak=%d" %
          (summary["domains_32_S3_total"], summary["domains_32_hard_and_override_total"],
           summary["domains_32_hard_and_weak_total"]))
    print("written: %s ; %s" % (WD / "_vi_probe_out.json", WD / "_vi_probe_out.txt"))


if __name__ == "__main__":
    main()
