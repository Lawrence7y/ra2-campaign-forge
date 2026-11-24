# -*- coding: utf-8 -*-
"""
_ef_fp_resample.py — 修版后精确率重抽样（第三步 (d)）。
· 样本 = 修版检测器在 15 件 .md 上的 findings 中人工抽取 33 条（跨 11 文件、F1/F2/F3）。
· 每条由本任务逐行读原文后独立判「真命中 / 误报」并给机制理由；**不沿用上一任务的
  13/19**（该 19 条样本中 KEFF:432/434/440 判真，与本任务判 LI:384 为误报所用的
  「整改/引用行」机制同类，属同机制双重标准，本样本按统一机制口径重判）。
· IS_MEASUREMENT = False：这是抽样估计，无全量人工标注。
运行： python -I -X utf8 <本文件>
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_fix_20261110")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
spec = importlib.util.spec_from_file_location("eq", HERE / "_ef_detector.py")
eq = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(eq)

FILES = [
    "lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md",
    "lead/tautology_audit_20261109/_ta_TAUTOLOGY_AUDIT_20261109.md",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md",
    "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md",
    "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md",
    "lead/metric_audit_20261109/_ma_METRIC_AUDIT.md",
    "lead/keff_calc_20261109/KEFF_CALC.md",
    "lead/keff_calc_20261109/_ke_REPORT.md",
    "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md",
    "lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md",
    "lead/gate_pipeline_20261109/_gp_DESIGN.md",
    "lead/score_decomp_20261109/SCORE_DECOMP.md",
    "lead/score_decomp_20261109/_sd_report.md",
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md",
    "lead/comparability_20261109/_cmp_AUDIT_20261109.md",
]

# (file, line, 判定, 理由)
SAMPLE = [
    ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 108, "真命中",
     "canonical G3a：本件自己的「决定性集合等式」标签直接实跑输出 set equal? True/18 个 id 恰好等于，同行无范围词；TAUTOLOGY_AUDIT.md:474 逐字点名此违规形态"),
    ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 107, "真命中",
     "canonical G3c：38/38=1 全称口吻 + 实跑输出，同行无范围词（TAUTOLOGY_AUDIT.md:453 S8 判全称已构造性证伪）"),
    ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 109, "真命中（弱）",
     "同 :107/:108 块的第 4 条（Fréchet 取等观测），同行无范围词；强度信号借自 :108——与 G3c 借用结构同型，按门禁格式层判真"),
    ("lead/metric_audit_20261109/_ma_METRIC_AUDIT.md", 76, "真命中",
     "同 MC:107 型：本件自己的零增量主张 + P=38/38=1，同行无范围词（实测而非假定≠范围声明）"),
    ("lead/metric_audit_20261109/_ma_METRIC_AUDIT.md", 77, "真命中",
     "同 MC:108 型：决定性集合等式 + 18 个 id 恰好等于，同行无范围词"),
    ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 149, "真命中",
     "canonical G3b：S5「R12 增量判别力 = 0 bit」全称 + 38/38=1.000，TAUTOLOGY_AUDIT.md:450 判全称已证伪"),
    ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 294, "真命中",
     "canonical S5 依据：本件自己的三层分类表行（R12 不独立 + P=1.000 增量 0 bit）；无文件名指针/无整改语气，K9 正确未误伤（修版 (c) 的反例保护目标）"),
    ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 302, "真命中",
     "canonical S5 依据：0.0 bit 裸全称（后验 0.1667→0.1667），TAUTOLOGY_AUDIT.md:393 引为证伪对象"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 388, "真命中（弱）",
     "「=实质条件·纯计数恒等式（已证）」强度词直接 38/74 计数、同行无范围词；按其自家规约（TA:700）强度词须跟「本N行观测」——格式层违规成立；「已证」在强度词表内，语义上属审计分类用语，边界如实记"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 396, "真命中（弱）",
     "裸等价声明「该空集 ⟺ B⊆A」+ 实跑证据、同行无范围词；与 G3c 同构（观测证据+借入强度信号+无同行范围）——格式层违规成立"),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 54, "真命中（弱）",
     "本件自己的裸集合全等声明「18 个 id 逐个对齐全等」，行/窗内无两半拆分；与 CA:158/S10 判例同类（格式层：数值对、两半结构缺）"),
    ("lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md", 88, "真命中（弱）",
     "同 LI:54：证明件自己的裸全等声明 + 输出引用，行内无两半拆分"),
    ("lead/keff_calc_20261109/KEFF_CALC.md", 432, "误报",
     "整改清单行：引用 EI:149 的声明并要求其标观测（「→ 1.000 是观测值非定理，须标…」）；与上一任务自判误报的 LI:384（整改表行）同机制——原抽样判真系同机制双重标准，本样本按统一口径改判误报"),
    ("lead/keff_calc_20261109/KEFF_CALC.md", 434, "误报",
     "同 :432：整改清单第 11 条（引 EI:294 表格并要求改标）"),
    ("lead/keff_calc_20261109/KEFF_CALC.md", 440, "误报",
     "同 :432：整改清单第 15 条（引 _cs_BASELINE_ALIGNMENT:334 并要求标观测值）"),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 267, "误报",
     "「决定性」作方法名（方法 A（决定性、结构性）——依赖图…）；上一任务已自认缺口「决定性作方法名」，修版未修（结构上限：与方法名/标签同字面）"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 356, "误报",
     "禁用串自检清单：被禁串的字面回显（门禁要防的正是这些串出现在断言位，清单位是引用）——mention 非 use"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 366, "误报",
     "强模式扫描命令与 29 串清单回显——mention 非 use"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 474, "误报",
     "批判性转述行：本行正是在指责 MC:108 的形态（「把实跑 set equal? True 直接接决定性标签，中间无范围声明」）——引用违规实例行被判为违规实例"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 610, "误报",
     "撤回范围声明行：「被撤回的是三个强度标签…；18=18、38/38=1 数值全部成立、不撤回」——自带限定语义；词表缺口：CORRECTION 缺「撤回」（只有「须撤回」）"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 434, "误报",
     "明写「不对称包含，不是恒等」「观测相等，措辞未升级为定理，风险低」——自带否定与范围语义；词表缺口：CORRECTION 缺「不是恒等」、SCOPE 缺「观测相等」"),
    ("lead/keff_calc_20261109/KEFF_CALC.md", 325, "误报",
     "「1.000 不能当定理」——本行就在否定定理化；词表缺口：CORRECTION 缺「不能当定理」（只有「不是定理」）"),
    ("lead/keff_calc_20261109/KEFF_CALC.md", 311, "误报",
     "设问标题「5.1 P=1.000 是精确还是观测」——「A还是B」无「究竟」前缀未入 QUESTION；标题行非断言"),
    ("lead/keff_calc_20261109/_ke_REPORT.md", 96, "误报",
     "评估标题行「## 4 『R12 增量 0 bit』评估（第四步）」——标题引用被评估对象"),
    ("lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md", 247, "误报",
     "「等价于」用于算子定义（朴素并集≈「任一层先报即算」的建模等价），带实跑证据 file:line；非观测等式的定理化"),
    ("lead/score_decomp_20261109/SCORE_DECOMP.md", 122, "误报",
     "「结构完全相同」用于改写相似性判断（GP-C06 同族），论域外（非集合/等式断言）"),
    ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", 37, "误报",
     "only_A 是字段名子串（ids_only_A 3 条）——E_EQ_STRICT 子串命中标识符；本行是命名约定说明"),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 52, "误报",
     "「输出：A_n 18 B_n 18 A==B True only_A [] only_B []」——无围栏的运行输出回显行（与 CA:158 同类但作者未放围栏）；修版 (a) 只豁免围栏内"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 617, "误报",
     "两段式模板/示范行（「A = B∩{r12=PASS} 的定义重言式、零信息量；非平凡半 B⊆A 等价于…」——教正确写法的示例），强度信号借自邻行；模板位 mention 非 use"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 629, "误报",
     "纠偏指令行：「前件 :146 的等价性断言（改列 A=B ⟺ P(r12|r10&n13)=1，LAYER_IDENTITY.md:376）」——QUOTE_OR_REVIEW 缺「改列」动词变体"),
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 642, "误报",
     "「本 74 行观测等式…A=B 的正确等价式是」——同行自带范围声明，本应被 (d2) 豁免，但 :643 的 38/38=1 在 ±2 内借入 I（I 借用阻断 scope_qualified_eq）；残留机制如实记"),
    ("lead/metric_audit_20261109/_ma_METRIC_AUDIT.md", 151, "误报",
     "错置判定表行（「★ 错置（同名异义）」——评审判定表）；K9 的 SOURCE_PTR 要求 文件名.ext:，裸「:214」指针变体未覆盖"),
    ("lead/comparability_20261109/_cmp_AUDIT_20261109.md", 115, "误报",
     "变更面清单表行（本件自己的盘点表，证据指针 `_cmp_assert_out.json` 无冒号行号）——K9 判据的指针形态变体未覆盖"),
]


def main() -> int:
    scans = {relp: eq.scan_file(ROOT / relp) for relp in FILES}
    idx: dict[str, dict] = {}
    for relp, rec in scans.items():
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            for x in rec[bucket]:
                idx[f"{relp}:{x['line']}"] = x
    rows = []
    n_true = n_false = 0
    for relp, n, label, why in SAMPLE:
        fl = f"{relp}:{n}"
        h = idx.get(fl)
        is_finding = bool(h and h["verdict"] == "FAIL")
        rows.append({
            "file:line": fl, "human_label": label, "why": why,
            "actual_verdict": h["verdict"] if h else "NO_RECORD",
            "actual_failure_type": h["failure_type"] if h else None,
            "actual_text": h["text"] if h else None,
            "is_finding_in_after_run": is_finding,
        })
        if not is_finding:
            continue
        if label.startswith("真命中"):
            n_true += 1
        elif label == "误报":
            n_false += 1
    n_finding_samples = n_true + n_false
    precision = round(n_true / max(1, n_finding_samples), 4)
    out = {
        "IS_MEASUREMENT": False,
        "sample_size_requested": len(SAMPLE),
        "n_samples_confirmed_findings": n_finding_samples,
        "n_true": n_true, "n_false": n_false,
        "precision_estimate": precision,
        "precision_basis": (
            f"修版后 findings 全量 144 条中人工抽样 {n_finding_samples} 条逐条判定："
            f"真命中 {n_true} / 误报 {n_false}；把抽样误报率外推到全量属估计不是测量。"
            "口径：门禁查格式合规性（观测等式接强度标签且同行无范围声明、裸等式声明无两半拆分）；"
            "「mention 非 use」（清单回显/整改意见/批判性转述/标题/命令回显/模板行）一律判误报；"
            "对上一任务 13/19 样本中 KEFF:432/434/440 的判真按统一机制口径改判误报（与该样本自判"
            " LI:384 误报同机制），不沿用 13/19。"),
        "residual_fp_mechanisms": [
            "mention-vs-use（TA/_ta 审计件自指：清单回显/批判性转述/模板行/分类学表）——结构上限",
            "词表缺口：CORRECTION 缺 撤回/不是恒等/不能当定理；SCOPE 缺 观测相等/裸观测；QUESTION 缺 无「究竟」的「A还是B」标题问句",
            "K9 指针形态变体：裸 :214 与无冒号 json 指针不匹配 SOURCE_PTR；非表格整改清单行（KEFF:432 类）整体未覆盖",
            "E_EQ_STRICT 子串命中标识符（ids_only_A）与论域外「完全相同/等价于」（改写相似性/算子定义）",
            "I 借用（±2）阻断 (d2) 范围豁免（TA:642）；「决定性」作方法名（LI:267）；无围栏输出回显（LI:52）",
        ],
        "rows": rows,
    }
    (HERE / "_ef_fp_resample_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"重抽样：{n_finding_samples} 条确认为修版后 findings（请求 {len(SAMPLE)}），"
          f"真命中 {n_true} / 误报 {n_false}，精确率估计 = {precision}（IS_MEASUREMENT=False）")
    for r in rows:
        print(f"  [{r['human_label']}] {r['file:line']} -> {r['actual_verdict']}/{r['actual_failure_type']}"
              + ("" if r["is_finding_in_after_run"] else "  (非 findings，未计入)"))
    print("written:", HERE / "_ef_fp_resample_out.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
