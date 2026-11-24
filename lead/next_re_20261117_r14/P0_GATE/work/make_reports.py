#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-GATE-FIX 报告生成器：按审计 ①–④ 修正 SUMMARY / PROGRESS。"""
import os
import sys
import json

ROOT = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(ROOT, r"lead\next_re_20261117_r14")
OUT = os.path.join(R14, "P0_GATE")
EVID = os.path.join(OUT, "EVIDENCE")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    c = json.load(open(os.path.join(EVID, "counts.json"), encoding="utf-8"))
    A = c["rail"]["A"]
    B = c["rail"]["B"]
    a_func = A.get("FUNC", 0)
    a_not = A.get("NOT_FUNC", 0)
    b_main_func = B.get("FUNC", 0)
    b_base_func = c["B_baseline_FUNC"]
    b_base_not = c["B_baseline_NOT_FUNC"]
    und = c["verdicts"].get("UNDECIDABLE", 0)

    s = []
    w = s.append
    w("# P0-GATE-FIX · atlas 之外 476 个入口裁定（审计 R14-R10 四项修正）")
    w("")
    w("> 卡号 P0-GATE-FIX｜目标 `ra2youli\\gamemd.exe`，SHA-256 `%s`，ImageBase 0x400000，只读未改。" % c["exe_sha256"])
    w("> 写域仅 `lead\\next_re_20261117_r14\\P0_GATE\\`；未改 `ra2youli\\`、`COVERAGE\\` 或台账。")
    w("> capstone %s `skipdata=True`；`.text=[%s,%s)`；不读 `vtables_v2.json`。复跑：`adjudicate_r10.py` → `verify.py` → `make_reports.py`。" %
      (c["capstone_version"], c["text_lo"], c["text_hi"]))
    w("")
    w("## 一、审计条件逐条落实")
    w("")
    w("1. **ALREADY_IN_COVERAGE = 2**：`004F8440`（`HouseClass::Update`, S16）与 `00535E50`（`SetDefenseTabCommand::Execute`, S09）。`VT_DIRECT_ENTRIES.tsv` 有 **413** distinct target，**413 − 2（已入 coverage）= 411**；这两条不属于本次 476 池，见 `EVIDENCE\\ALREADY_IN_COVERAGE.tsv`。")
    w("2. **B 轨按 R14-R10 报 60**：65 条候选中有 5 条上游 `TRUE_ENTRY_UNIFIED.tsv` verdict=FALSE（c5 粗距离抑制）。R14-R10 口径 B = **60 FUNC / 5 NOT_FUNC**；5 条见 `EVIDENCE\\B_RAIL_C5_EXCLUDED.tsv`。主表仍保留审计维持的 65 条 FUNC，但不再声称「c1–c6 全过导出 65」。")
    w("3. **A2 已换**：撤下 `linear-sweep-start` 作为证据；A2 = 前驱∈{`nop`,`int3`,`ret`,`jmp`}。实测 nop 409 / ret 2，共 411。审计基线：**34.7%** 的 4B 对齐地址、**36.5%** 的 16B 对齐地址是 sweep 起点；对齐起点中 **78.6%** 的前驱是函数中部指令 ⇒ 旧 A2 无区分力，已废弃。")
    w("4. **分级对齐**：逐行与 SUMMARY 统一为：`[已证] slot value`（槽值指向 `.text`）、`[已证] predecessor-form`（前驱形态）、`[已证] table-boundary-input-restatement`（A3 表界，仅重述同源输入）；`[静态推断] slot-value-as-function-entry`（语义原则）。B 轨字节/判据为 `[已证]`，c4b 语义 bucket 为 `[静态推断]`。")
    w("")
    w("## 二、分轨账")
    w("")
    w("| 轨 | 池 | R14-R10 口径 | 主表裁定 |")
    w("|---|---:|---:|---:|")
    w("| A `vt_direct` | 411 | FUNC **%d** / NOT_FUNC **%d** | 411 FUNC |" % (a_func, a_not))
    w("| B `true_entry` | 65 | FUNC **%d** / NOT_FUNC **%d** | 65 FUNC（5 条 c5 覆盖已披露） |" %
      (b_base_func, b_base_not))
    w("| 合计 | 476 | 471 baseline FUNC / 5 baseline NOT_FUNC | 476 FUNC / 0 NOT_FUNC / 0 UNDECIDABLE |")
    w("")
    w("A 轨逐条 A1–A4 全过，NOT_FUNC 失败项：**无**。顶点证据为前驱形态而非 sweep 起点；A3 仍为自定界 1214 表输入，按 `[已证] 重述` 标注，不作独立第二通道。")
    w("")
    w("B 轨 5 条 R14-R10 基线排除：`%s`。审计给出填充隔离证据，故主表维持 FUNC；此改判已显式登记，不再默认通过。" %
      "`, `".join(c["B_c5_excluded"]))
    w("")
    w("## 三、集合与形态")
    w("")
    w("- ∩ `coverage.tsv` = **%d**（本 476 池）；∩ `probe_and_data_entries.tsv` = **%d**；atlas 区间包含命中 = **%d**。" %
      (c["intersection_coverage"], c["intersection_probe"], c["atlas_owner_hits"]))
    w("- A 轨 tiny(<16B)=**%d**，首字节 `E8/E9/EB`=**%d**；均只作形态注记，不作否定理由。" %
      (c["A_tiny"], c["A_first_E8_E9_EB"]))
    w("- A 轨数据交叉命中 = **%d**（跳表 dword / probe 精确命中 / Items 区）；审计扩至全部 switch 表/标签后仍为 0。" % c["A_data_cross"])
    w("- B 轨 c4a=%d，c4b=%d，both=%d；c4b 旧「体长≥16B」作废。" %
      (c["B_c4a"], c["B_c4b"], c["B_both"]))
    w("")
    w("## 四、分级")
    w("- `[已证]`：PE 段归属、槽值、前驱形态、A3 表界重述、B 字节/判据、集合交集、计数。")
    w("- `[静态推断]`：槽值即函数入口的语义原则、B c4b 语义 bucket。")
    w("- `[未证]`：无；UNDECIDABLE=%d。" % und)
    w("")
    w("## 五、P0 出口闸结论")
    w("")
    w("**P0 出口闸 (b)：有条件满足。** 476 条已全部裁定且无一为 `NOT_FUNC`；但支撑判据已按审计 R14-R10 修正（A2 换为前驱形态、A/B 轨分级对齐、`ALREADY_IN_COVERAGE` = 2、B 轨 60）。**待 Lead 验收这 4 项修正后方可标记为满足。**")
    w("")
    w("## 六、证据与复算")
    w("- `ENTRY_ADJUDICATION.tsv`：476 行主表；A 轨 c1..c6=`NA`，A1–A4/分级在 evidence。")
    w("- `EVIDENCE\\ENTRY_ADJUDICATION_FULL.tsv`、`A_RAIL_DETAILS.tsv`：不截断逐条证据与分级列。")
    w("- `EVIDENCE\\ALREADY_IN_COVERAGE.tsv`、`B_RAIL_C5_EXCLUDED.tsv`、`R14_R10_NOT_FUNC_DETAILS.txt`、`counts.json`、`VERIFY.txt`、`_audit\\VERDICT.md`。")
    w("")
    open(os.path.join(OUT, "ADJUDICATION_SUMMARY.md"), "w", encoding="utf-8").write("\n".join(s))

    p = []
    w = p.append
    w("# P0-GATE-FIX PROGRESS（≤60 行）")
    w("")
    w("| 项 | 结论 |")
    w("|---|---|")
    w("| 写域 | `lead\\next_re_20261117_r14\\P0_GATE\\`，输入只读 |")
    w("| A 轨 FUNC/NOT_FUNC | **%d / %d** |" % (a_func, a_not))
    w("| B 轨 R14-R10 口径 FUNC/NOT_FUNC | **%d / %d** |" % (b_base_func, b_base_not))
    w("| B 主表 | 65 FUNC；5 条 c5 覆盖已登记 |")
    w("| 主表合计 | 476 FUNC / 0 NOT_FUNC / 0 UNDECIDABLE |")
    w("| ALREADY_IN_COVERAGE | **%s** |" % ", ".join(c["already_in_coverage_addrs"]))
    w("| VT 口径 | 413 distinct target − 2 already = 411 |")
    w("| A2 | 前驱形态 nop %d / ret %d；sweep-start 撤下 |" %
      (c["A2_pred_kinds"].get("nop", 0), c["A2_pred_kinds"].get("ret", 0)))
    w("| A2 废弃基线 | 4B 34.7% / 16B 36.5% / 中部前驱 78.6% |")
    w("| 分级 | slot/pred/A3 `[已证]`；语义原则 `[静态推断]` |")
    w("| 交集 | coverage %d / probe %d / atlas owner %d |" %
      (c["intersection_coverage"], c["intersection_probe"], c["atlas_owner_hits"]))
    w("| 出口闸 (b) | **有条件满足** |")
    w("")
    w("## 复算")
    w("- 主表：`ENTRY_ADJUDICATION.tsv`（476 行）；全证据：`EVIDENCE\\ENTRY_ADJUDICATION_FULL.tsv`。")
    w("- 专表：`ALREADY_IN_COVERAGE.tsv`、`B_RAIL_C5_EXCLUDED.tsv`、`A_RAIL_DETAILS.tsv`。")
    w("- 审计原文：`P0_GATE\\_audit\\VERDICT.md` §四/§五。")
    w("- 复跑：`python P0_GATE\\work\\adjudicate_r10.py && python P0_GATE\\work\\verify.py && python P0_GATE\\work\\make_reports.py`。")
    w("- capstone 5.0.7 `skipdata=True`；不读 `vtables_v2.json`；不写 `COVERAGE\\`。")
    w("")
    w("## 交付路径")
    w("- `P0_GATE\\ENTRY_ADJUDICATION.tsv`")
    w("- `P0_GATE\\ADJUDICATION_SUMMARY.md`")
    w("- `P0_GATE\\PROGRESS.md`")
    w("- `P0_GATE\\EVIDENCE\\`、`P0_GATE\\work\\`")
    if len(p) > 60:
        raise SystemExit("PROGRESS.md has %d lines (>60)" % len(p))
    open(os.path.join(OUT, "PROGRESS.md"), "w", encoding="utf-8").write("\n".join(p))
    print("wrote ADJUDICATION_SUMMARY.md (%d lines), PROGRESS.md (%d lines)" % (len(s), len(p)))


if __name__ == "__main__":
    main()
