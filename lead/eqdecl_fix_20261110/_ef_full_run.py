# -*- coding: utf-8 -*-
"""
_eq_full_run.py — 第四步：全量跑（不是只跑 9 个）

(a) 对第一步清点出的全部恒等类断言行（编排方【编排方实跑：恒等类断言清点】45 行 /
    7 文件）跑一遍；并扩到 8 个只读目录的全部 .md（15 件）作覆盖核对。
    给总 findings 数与按文件 / 按失败型分布。
(b) 逐条给「真命中」与「误报」的抽样判定（≥15 条，含两边）；误报逐条说明为什么。
(c) 精确率与召回率的**估计**（明确标注：估计不是测量，无人工全量标注）。
(d) 漏检明显时如实记原因。

运行： python -I -X utf8 <本文件>  → _eq_full_out.json（全量结果）
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from collections import Counter

# 修版 harness（仅参数化两处 + 抽样开关，其余逐字同原件）：
#   python -I -X utf8 _ef_full_run.py --det <abs detector.py> --out <abs json> [--sample orig|none]
#   --sample orig：沿用上一任务 sample_specs 的 18 条标签（仅用于 before 复现基线）；
#   --sample none：抽样判定移交 _ef_fp_resample.py（修版后的重抽样，≥20 条，逐条重判）。
HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_fix_20261110")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
_argv = sys.argv[1:]


def _arg(flag: str, default: str) -> str:
    return _argv[_argv.index(flag) + 1] if flag in _argv else default


MOD_PATH = pathlib.Path(_arg("--det", str(HERE / "_ef_detector.py")))
OUT_PATH = pathlib.Path(_arg("--out", str(HERE / "_ef_full_out.json")))
SAMPLE_MODE = _arg("--sample", "none")
_spec = importlib.util.spec_from_file_location("_eq_detector", MOD_PATH)
eq = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(eq)

# 编排方清点里的 4 个文件 + 本任务扩展到 8 个只读目录
LISTED_FILES = [
    "lead/layer_identity_20261109/LAYER_IDENTITY.md",
    "lead/keff_calc_20261109/KEFF_CALC.md",
    "lead/score_decomp_20261109/SCORE_DECOMP.md",
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md",
]
READ_DIRS = [
    "lead/tautology_audit_20261109",
    "lead/layer_identity_20261109",
    "lead/metric_audit_20261109",
    "lead/keff_calc_20261109",
    "lead/evidence_indep_20261109",
    "lead/gate_pipeline_20261109",
    "lead/score_decomp_20261109",
    "lead/comparability_20261109",
]

# 编排方【编排方实跑：恒等类断言清点】逐字登记的 45 行（7 文件，另含
# comparability_20261109/COMPARABILITY_AUDIT.md:158）。此处按该清点逐字转录行号。
LISTED_LINES = {
    "lead/layer_identity_20261109/LAYER_IDENTITY.md": [
        1, 13, 22, 26, 87, 104, 110, 112, 116, 122, 126, 127, 128, 182, 189,
        197, 200, 208, 213, 216, 223, 225, 226, 228, 233, 234, 242, 273, 279,
        304, 326, 337, 338, 339, 365, 372, 376, 393, 400, 409, 414],
    "lead/keff_calc_20261109/KEFF_CALC.md": [340],
    "lead/score_decomp_20261109/SCORE_DECOMP.md": [135, 239],
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md": [158],
}


def main() -> int:
    md_files = sorted({p for d in READ_DIRS for p in (ROOT / d).glob("*.md")})
    all_recs = [eq.scan_file(p) for p in md_files]

    # ---- (a) 总 findings 数与按文件 / 按失败型分布 ----
    total_findings = sum(r["n_findings"] for r in all_recs)
    total_anchors = sum(r["n_anchors"] for r in all_recs)
    total_skips = sum(r["n_skips"] for r in all_recs)
    total_undec = sum(r["n_undecidables"] for r in all_recs)
    total_taut = sum(r["n_tautology_ok"] for r in all_recs)
    total_passes = sum(r["n_passes"] for r in all_recs)

    by_file = {}
    for r in all_recs:
        by_file[r["file"]] = {
            "bytes": r["bytes"], "sha256": r["sha256"],
            "n_lines": r["n_lines"], "n_anchors": r["n_anchors"],
            "n_findings": r["n_findings"],
            "findings_by_type": r["findings_by_type"],
            "n_tautology_ok": r["n_tautology_ok"],
            "n_passes": r["n_passes"], "n_skips": r["n_skips"],
            "n_undecidables": r["n_undecidables"],
            "skip_by_reason": r["skip_by_reason"],
        }
    by_ftype: Counter = Counter()
    for r in all_recs:
        by_ftype.update(r["findings_by_type"])

    # ---- 对编排方清点 45 行的逐行覆盖核对 ----
    rec_by_file = {r["file"]: r for r in all_recs}
    listed_rows = []
    for relp, lines in LISTED_LINES.items():
        r = rec_by_file.get(relp)
        if r is None:
            listed_rows.append({"file": relp, "error": "file_not_scanned"})
            continue
        all_hits = (r["findings"] + r["passes"] + r["tautology_ok"] +
                    r["skips"] + r["undecidables"])
        idx = {x["line"]: x for x in all_hits}
        for n in lines:
            h = idx.get(n)
            listed_rows.append({
                "file:line": f"{relp}:{n}",
                "anchored": h is not None,
                "verdict": h["verdict"] if h else "NOT_AN_ANCHOR",
                "failure_type": h["failure_type"] if h else None,
                "category": h["category"] if h else None,
                "text": h["text"] if h else None,
                "skip_reason": h.get("skip_reason") if h else None,
                "flags": h["flags"] if h else None,
            })
    n_listed = len(listed_rows)
    n_listed_anchored = sum(1 for x in listed_rows if x["anchored"])
    n_listed_findings = sum(1 for x in listed_rows if x["verdict"] == "FAIL")

    # ---- (b) 抽样 ≥15 条：真命中 / 误报，逐条判定 ----
    # 人工判定依据：本会话实读的原文行 + 上游 TAUTOLOGY_AUDIT.md §4.3 判定表 +
    # 编排方【任务】三关期望。**这是人工抽样判定，不是全量标注。**
    sample_specs = [
        # (file, line, bucket, 判定, 理由)
        ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 108, "findings", "真命中",
         "逐字「**决定性集合等式**」+「实跑命令 2 输出 … set equal? True … 18 个 id 恰好等于」，强度标签直接接观测证据、同行无范围词；TAUTOLOGY_AUDIT.md:474「同模式复发的共有根」逐字点名此行 ⇒ F3 正确"),
        ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 107, "findings", "真命中",
         "逐字「⇒ P(r12=PASS\\|n13=PASS)=38/38=1」+ 同窗 :108「决定性」；TAUTOLOGY_AUDIT.md:453 S8 判「实质条件·全称已构造性证伪」⇒ F3 正确"),
        ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 149, "findings", "真命中",
         "逐字「**R12 增量判别力 = 0 bit**：P(…)=38/38=1.000」全称口吻 + 观测数值，同行无范围；TAUTOLOGY_AUDIT.md:450 S5 判全称已证伪 ⇒ F3 正确"),
        ("lead/keff_calc_20261109/KEFF_CALC.md", 432, "findings", "真命中",
         "逐字「EVIDENCE_INDEPENDENCE.md:149『R12 增量判别力 = 0 bit：P(…)=38/38=1.000』」—— 与 S5 同形态的观测等式转述，无范围声明；按门禁格式仍须声明 ⇒ F3（属于「引用行是否应豁免」的边界，见 (d)）"),
        ("lead/keff_calc_20261109/KEFF_CALC.md", 434, "findings", "真命中",
         "逐字「P(…)=1.000，增量 0 bit」同上，S5 同族 ⇒ F3"),
        ("lead/keff_calc_20261109/KEFF_CALC.md", 440, "findings", "真命中",
         "逐字「P(…)=1.000，R12 增量信息 0 bit」同上 ⇒ F3"),
        ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 294, "findings", "真命中",
         "逐字表格「P(r12=PASS|n13=PASS)=1.000，增量 **0 bit**」；TAUTOLOGY_AUDIT.md:450 列 S5 依据含 :294 ⇒ F3"),
        ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 302, "findings", "真命中",
         "逐字「`R12` 增量信息 **0.0 bit**（后验 0.1667→0.1667）」同上 ⇒ F3"),
        ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 126, "findings", "误报",
         "该行是**上游审计的错置判定表**（逐字「| 6 | CHAIN_VS_SINGLE.md:214 | … | 上游审计断言… | **错置** | **证据不足，降级存疑** …」），含 38/38=1.000 但它是在**讨论**该数值的口径，不是本件把观测等式升级为定理；检测器按字面 38/38 + 1.000 命中 ⇒ 误报。原因：QUOTE_OR_REVIEW 未覆盖「错置 / 降级存疑」这类评审语气"),
        ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 356, "findings", "误报",
         "逐字「- [ ] 禁用串自检：`决定性集合等式 / 两个自由度 / 38/38 为定理 / B⊆A⟺P(r12|n13)=1`」—— 这是 §3.4 **检查清单里的禁用串清单**（任务要防的正是这些串），不是本件把观测等式写成定理；检测器按字面命中 ⇒ 误报。注：TAUTOLOGY_AUDIT.md:760-763 自记门禁曾因把禁用串写进输出示例而误触发，同因"),
        ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 366, "findings", "误报",
         "逐字「- **强模式扫描**：25 份 `.md`（`恒等/重言/决定性/必相等/恒真/恒成立/完全相同/A==B/取等/一致率/0 bit/...` 等 29 串）」—— 这是**普查命令的强模式串清单**，不是断言；检测器按字面命中 ⇒ 误报。原因：形态清单/命令回显行未豁免"),
        ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 384, "findings", "误报",
         "逐字整改表「| 9 | 前件 :110,194,... | 「只剩 1 个非 1 因子 …」→ 改「在 `n13` 优先的链式因子化下…乘积恒 `1/13`，**不能当自由度或独立层**」」—— 这是**整改意见行**（要求把错误措辞改掉），不是本件犯的错；检测器按字面命中 ⇒ 误报。原因：K5 纯转述豁免要求 `not E and not O`，而该行含 E/O 形态"),
        ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 21, "findings", "误报",
         "逐字「| # | 命令 | 输出要点 |」—— 这是**空表头行**，因窗口（±8 行）吸收了邻行 :24 的 `n= 74 / 1.000` 等观测数值被误判 F1；本行自身无任何恒等类断言 ⇒ 误报。原因：F1 用整窗 T/S 而非锚点局部 T/S，空表头被邻行数据连坐"),
        ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 267, "findings", "误报",
         "逐字「**方法 A（决定性、结构性）—— 依赖图源节点数 + A1–A5 五检**：」—— 「决定性」是**方法名**（structural），且窗口内含 38/38 类观测；该行不是把观测等式接强度标签 ⇒ 误报。原因：INTENSITY 未区分「决定性」作方法名与作定理标签"),
        ("lead/keff_calc_20261109/KEFF_CALC.md", 314, "passes", "真命中（负向）",
         "逐字「⇒ P(…)=38/38=1.000 是**本 74 行上的观测值，不是精确 1.000、不是定理**」—— 同行有范围 + 明确否定 ⇒ CORRECTLY_SCOPED，不报 F3。这是负控生效的真命中"),
        ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 104, "tautology_ok", "真命中（负向）",
         "逐字「`A ⊆ B` 是去掉一个合取项的重言式」⇒ TAUTOLOGY_OK，不猜为实质条件。关一 G1a"),
        ("lead/score_decomp_20261109/SCORE_DECOMP.md", 235, "tautology_ok", "真命中（负向）",
         "逐字「**恒真兜底在正类样本上的必然命中，信息量 = 0**」⇒ TAUTOLOGY_OK。关一 G1c"),
        ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 104, "passes", "真命中（负向）",
         "逐字「根因不是…而是 **R12 不是独立证据根**」正确否定句 ⇒ SUBSTANTIVE_OK，不报 F1/F2/F3。关二 G2a"),
        ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", 158, "findings", "真命中",
         "逐字「chain_changed=18 | unresolved_changed=18 | 集合恒等? True」裸集合等式、两半全缺 ⇒ F1。注：TAUTOLOGY_AUDIT.md:455 S10 判「措辞未升级为定理，风险低」，但门禁查**格式合规性**，F1 属格式缺失而非语义错误 ⇒ 仍算真命中（边界见第五步）"),
    ]
    samples = []
    if SAMPLE_MODE == "orig":
        for relp, n, bucket, label, why in sample_specs:
            r = rec_by_file.get(relp)
            h = None
            if r:
                h = next((x for x in r[bucket] if x["line"] == n), None)
            samples.append({
                "file:line": f"{relp}:{n}",
                "bucket": bucket,
                "human_sample_label": label,
                "why": why,
                "actual_verdict": h["verdict"] if h else "NOT_IN_BUCKET",
                "actual_failure_type": h["failure_type"] if h else None,
                "text": h["text"] if h else None,
                "matched_strings": h["matched_strings"] if h else None,
                "evidence_matches": (h.get("evidence_matches") or [])[:4] if h else None,
            })

    n_true = sum(1 for s in samples if s["human_sample_label"].startswith("真命中"))
    n_false = sum(1 for s in samples if s["human_sample_label"] == "误报")
    # ---- (c) 精确率 / 召回率「估计」 ----
    # 估计口径：抽样中误报比例外推到全量 findings（不是测量）；
    # 召回率以「三关 9 案例 9/9 + 编排方清点 45 行中被判 FAIL 的行」为可见上界，
    # 因无人工全量标注，真值未知 ⇒ 明确标注 estimate。
    est_precision = round(n_true / max(1, n_true + n_false), 4)
    out = {
        "scope": {
            "read_dirs": READ_DIRS,
            "n_md_files": len(md_files),
            "md_files": [eq.rel(p) for p in md_files],
            "listed_files": LISTED_FILES,
            "listed_n_lines": sum(len(v) for v in LISTED_LINES.values()),
            "window_radius": eq.WINDOW_RADIUS,
            "local_radius": eq.LOCAL_RADIUS,
        },
        "totals": {
            "n_files": len(all_recs),
            "n_anchors": total_anchors,
            "n_findings": total_findings,
            "n_tautology_ok": total_taut,
            "n_passes": total_passes,
            "n_skips": total_skips,
            "n_undecidables": total_undec,
            "skipped_total": total_skips + total_undec,
        },
        "findings_by_type": dict(by_ftype),
        "by_file": by_file,
        "listed_45_lines": {
            "n_rows": n_listed,
            "n_anchored": n_listed_anchored,
            "n_not_anchored": n_listed - n_listed_anchored,
            "n_findings": n_listed_findings,
            "rows": listed_rows,
        },
        "sampling": {
            "sample_mode": SAMPLE_MODE,
            "note": ("orig=沿用上一任务 18 条标签仅复现基线；修版后的精确率重抽样"
                     "（≥20 条逐条重判）见 _ef_fp_resample.py，不沿用 13/19"
                     if SAMPLE_MODE != "orig" else
                     "before 基线复现：沿用上一任务 18 条标签"),
            "n_samples": len(samples),
            "n_true_positive_sample": n_true,
            "n_false_positive_sample": n_false,
            "samples": samples,
        },
        "precision_recall_estimate": {
            "IS_MEASUREMENT": False,
            "precision_estimate_from_sample": est_precision,
            "precision_basis": (f"抽样 {len(samples)} 条中真命中 {n_true} / 误报 {n_false}；"
                                "把抽样误报率外推到全量 findings，属估计不是测量"),
            "recall_estimate": "不可给数值（无人工全量标注，真值总数未知）",
            "recall_visible_lower_bound": {
                "three_gates": "9/9 通过（_eq_three_gates_out.json）",
                "listed_45_lines_findings": n_listed_findings,
                "note": "只是可见命中数，不是召回率分母",
            },
            "why_not_measured": ("本任务未做 15 件 .md 全量人工逐行标注；"
                                 "TAUTOLOGY_AUDIT.md:370 自记『未做全仓逐文件人工通读』；"
                                 "故精确率/召回率只能是估计，不得冒充实测"),
        },
        "per_file_full": [
            {"file": r["file"], "sha256": r["sha256"], "bytes": r["bytes"],
             "n_findings": r["n_findings"], "findings": r["findings"],
             "n_skips": r["n_skips"], "skip_by_reason": r["skip_by_reason"],
             "skips": r["skips"][:20]}
            for r in all_recs
        ],
    }
    dest = OUT_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("=== 全量跑 ===")
    print("md 文件数 =", len(md_files), " 锚点数 =", total_anchors,
          " findings =", total_findings, " tautology_ok =", total_taut,
          " passes =", total_passes, " skips =", total_skips,
          " undecidables =", total_undec)
    print("findings_by_type =", dict(by_ftype))
    print("按文件 findings：")
    for f, d in sorted(by_file.items(), key=lambda x: -x[1]["n_findings"]):
        if d["n_findings"]:
            print(f"  {d['n_findings']:3d}  {f}  {d['findings_by_type']}")
    print("编排方清点 45 行：anchored =", n_listed_anchored, "/", n_listed,
          " findings =", n_listed_findings)
    print("抽样：", len(samples), "条，真命中", n_true, "误报", n_false,
          " 精确率估计 =", est_precision)
    for s in samples:
        print(f"  [{s['human_sample_label']}] {s['file:line']} -> {s['actual_verdict']}/{s['actual_failure_type']}")
    print("written:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
