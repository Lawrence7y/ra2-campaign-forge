# -*- coding: utf-8 -*-
"""
_eq_three_gates.py — 三关 × 9 案例验收（第三步）

关一：真重言式必须报「重言式」，不是「实质条件」；且不得报 F1/F2/F3。
关二：真实质条件必须不误报 F1/F2/F3。
关三：观测等式写成定理必须报 F3。

9 个锚点全部取自被检文档真实 file:line（本会话实读），期望来自编排方【任务】
第三步 (a)(b)(c) 与 TAUTOLOGY_AUDIT.md:437-461 §4.3。

运行： python -I -X utf8 <本文件>   → 落盘 _eq_three_gates_out.json + 终端摘要
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

# 修版 harness（仅参数化两处，其余逐字同原件）：检测器路径与输出路径。
#   python -I -X utf8 _ef_three_gates.py --det <abs detector.py> --out <abs json>
HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_fix_20261110")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
_argv = sys.argv[1:]


def _arg(flag: str, default: str) -> str:
    return _argv[_argv.index(flag) + 1] if flag in _argv else default


MOD_PATH = pathlib.Path(_arg("--det", str(HERE / "_ef_detector.py")))
OUT_PATH = pathlib.Path(_arg("--out", str(HERE / "_ef_three_gates_out.json")))
_spec = importlib.util.spec_from_file_location("_eq_detector", MOD_PATH)
eq = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(eq)

# gate, case_id, S-case, 关/类别描述, rel, line, 期望判定, 期望失败型, 期望类别, 期望依据(实读/实跑来源)
CASES = [
    ("关一", "G1a", "S1 半 A⊆B",
     "lead/layer_identity_20261109/LAYER_IDENTITY.md", 104,
     "TAUTOLOGY_OK", None, "TAUTOLOGY",
     "LAYER_IDENTITY.md:104 逐字「`A ⊆ B` 是去掉一个合取项的重言式」；TAUTOLOGY_AUDIT.md:446 S1 行 / :465 真重言式清单"),
    ("关一", "G1b", "S3 :125 逻辑重言式",
     "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md", 125,
     "TAUTOLOGY_OK", None, "TAUTOLOGY",
     "前件 :125 逐字「`A ⊆ B` 是**去掉一个合取项的逻辑重言式**」；TAUTOLOGY_AUDIT.md:448 S3 行"),
    ("关一", "G1c", "S12 S3 DEFAULT 恒真兜底",
     "lead/score_decomp_20261109/SCORE_DECOMP.md", 235,
     "TAUTOLOGY_OK", None, "TAUTOLOGY",
     "SCORE_DECOMP.md:235 逐字「**恒真兜底在正类样本上的必然命中，信息量 = 0**」；TAUTOLOGY_AUDIT.md:457 S12 行"),
    ("关二", "G2a", "S2 :104 依赖图（正确否定句）",
     "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 104,
     "SUBSTANTIVE_OK", None, "SUBSTANTIVE",
     "METRIC_CONVENTION_AUDIT.md:104 逐字「根因不是…而是 **R12 不是独立证据根**」；TAUTOLOGY_AUDIT.md:447 S2 行「本身正确，不列入撤回对象」"),
    ("关二", "G2b", "S4 正确等价式 A=B ⟺ P(r12|r10&n13)=1",
     "lead/layer_identity_20261109/LAYER_IDENTITY.md", 128,
     "PASS_QUALIFIED", None, "SUBSTANTIVE",
     "LAYER_IDENTITY.md:128 逐字「**正确等价式**：`A = B ⟺ P(r12=PASS | r10=PASS & n13=PASS) = 1`」+「在 74 行上同真…额外巧合」；TAUTOLOGY_AUDIT.md:449 S4 行"),
    ("关二", "G2c", "S7 Fréchet min q_i 恰取等（定理部分）",
     "lead/keff_calc_20261109/KEFF_CALC.md", 262,
     "SUBSTANTIVE_OK", None, "SUBSTANTIVE",
     "KEFF_CALC.md:262 逐字「`P(allPASS|E) ≤ min q_i = min(...) = 0.076923`」；TAUTOLOGY_AUDIT.md:452 S7 行 / :413 第 4 处"),
    ("关三", "G3a", "S1「决定性集合等式」标签",
     "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 108,
     "FAIL", "F3", "SUBSTANTIVE",
     "METRIC_CONVENTION_AUDIT.md:108 逐字「3. **决定性集合等式**：实跑命令 2 输出 … `set equal? True` … 18 个 id **恰好等于**」；TAUTOLOGY_AUDIT.md:446 S1 行 / :474「直接接决定性标签，中间无范围声明」"),
    ("关三", "G3b", "S5「R12 增量 0 bit」全称",
     "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 149,
     "FAIL", "F3", "SUBSTANTIVE",
     "EVIDENCE_INDEPENDENCE.md:149 逐字「- **R12 增量判别力 = 0 bit**：`P(r12=PASS | n13=PASS) = 38/38 = 1.000`」；TAUTOLOGY_AUDIT.md:450 S5 行"),
    ("关三", "G3c", "S8「38/38」",
     "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 107,
     "FAIL", "F3", "SUBSTANTIVE",
     "METRIC_CONVENTION_AUDIT.md:107 逐字「⇒ `P(r12=PASS\\|n13=PASS)=38/38=1`」+ 同窗 :108「决定性」标签；TAUTOLOGY_AUDIT.md:453 S8 行"),
]

GATE_RULE = {
    "关一": "真重言式必须报「重言式」而不是「实质条件」；不得报 F1/F2/F3",
    "关二": "真实质条件必须不误报 F1/F2/F3",
    "关三": "观测等式写成定理必须报 F3",
}


def main() -> int:
    cache: dict[str, dict] = {}
    rows = []
    for gate, cid, scase, relp, line, exp_v, exp_f, exp_cat, source in CASES:
        if relp not in cache:
            cache[relp] = eq.scan_file(ROOT / relp)
        rec = cache[relp]
        hit = None
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            for r in rec[bucket]:
                if r["line"] == line:
                    hit = r
                    break
            if hit:
                break

        if hit is None:
            rows.append({
                "gate": gate, "case": cid, "s_case": scase,
                "file:line": f"{relp}:{line}", "expected": f"{exp_v}/{exp_f}/{exp_cat}",
                "actual": "NO_ANCHOR_RECORD", "passed": False,
                "note": "该行未被 M1–M5 形态命中 ⇒ 检测器无记录（如实记，不补造）",
                "source": source,
            })
            continue

        act_v, act_f, act_cat = hit["verdict"], hit["failure_type"], hit["category"]
        # 判通过：按各关规则，而不是简单字符串相等
        if gate == "关一":
            ok = (act_cat == "TAUTOLOGY" and act_f is None and act_v == "TAUTOLOGY_OK")
        elif gate == "关二":
            ok = (act_f is None and act_v in
                  ("SUBSTANTIVE_OK", "PASS_QUALIFIED", "CORRECTLY_SCOPED", "SKIP"))
        else:
            ok = (act_v == "FAIL" and act_f == "F3")
        # 同时核对期望类别（关三期望 SUBSTANTIVE）
        if exp_cat is not None and act_cat != exp_cat:
            ok = False

        rows.append({
            "gate": gate, "case": cid, "s_case": scase,
            "file:line": f"{relp}:{line}",
            "text": hit["text"],
            "expected_verdict": exp_v, "expected_failure_type": exp_f,
            "expected_category": exp_cat,
            "actual_verdict": act_v, "actual_failure_type": act_f,
            "actual_category": act_cat,
            "expected": f"{exp_v}/{exp_f or '-'}/{exp_cat}",
            "actual": f"{act_v}/{act_f or '-'}/{act_cat}",
            "passed": ok,
            "flags": hit["flags"],
            "missing": hit.get("missing"),
            "matched_strings": hit["matched_strings"],
            "window": hit["window"],
            "window_lines": hit["window_lines"],
            "skip_reason": hit.get("skip_reason"),
            "source": source,
            "evidence_matches": hit.get("evidence_matches", [])[:8],
        })

    matrix = {}
    for gate in ("关一", "关二", "关三"):
        gr = [r for r in rows if r["gate"] == gate]
        matrix[gate] = {
            "rule": GATE_RULE[gate],
            "cases": [r["case"] for r in gr],
            "passed": sum(1 for r in gr if r["passed"]),
            "total": len(gr),
            "all_passed": all(r["passed"] for r in gr),
        }
    out = {
        "detector": str(MOD_PATH),
        "window_radius": eq.WINDOW_RADIUS,
        "local_radius": eq.LOCAL_RADIUS,
        "n_cases": len(rows),
        "n_passed": sum(1 for r in rows if r["passed"]),
        "n_failed": sum(1 for r in rows if not r["passed"]),
        "gates": matrix,
        "matrix_rows": rows,
        "files_scanned": {k: {"sha256": v["sha256"], "bytes": v["bytes"],
                              "n_anchors": v["n_anchors"]}
                          for k, v in cache.items()},
    }
    dest = OUT_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"三关 × 9 案例：{out['n_passed']}/{out['n_cases']} 通过")
    for gate, m in matrix.items():
        print(f"  {gate}: {m['passed']}/{m['total']} all_passed={m['all_passed']}")
    print("  case | 期望 | 实际 | 通过")
    for r in rows:
        print(f"  {r['case']} {r['file:line']} | {r['expected']} | {r['actual']} | {r['passed']}")
    print("written:", dest)
    return 0 if out["n_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
