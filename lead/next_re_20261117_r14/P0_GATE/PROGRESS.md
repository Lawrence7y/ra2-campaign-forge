# P0-GATE-FIX PROGRESS（≤60 行）

| 项 | 结论 |
|---|---|
| 写域 | `lead\next_re_20261117_r14\P0_GATE\`，输入只读 |
| A 轨 FUNC/NOT_FUNC | **411 / 0** |
| B 轨 R14-R10 口径 FUNC/NOT_FUNC | **60 / 5** |
| B 主表 | 65 FUNC；5 条 c5 覆盖已登记 |
| 主表合计 | 476 FUNC / 0 NOT_FUNC / 0 UNDECIDABLE |
| ALREADY_IN_COVERAGE | **004F8440, 00535E50** |
| VT 口径 | 413 distinct target − 2 already = 411 |
| A2 | 前驱形态 nop 409 / ret 2；sweep-start 撤下 |
| A2 废弃基线 | 4B 34.7% / 16B 36.5% / 中部前驱 78.6% |
| 分级 | slot/pred/A3 `[已证]`；语义原则 `[静态推断]` |
| 交集 | coverage 0 / probe 0 / atlas owner 0 |
| 出口闸 (b) | **有条件满足** |

## 复算
- 主表：`ENTRY_ADJUDICATION.tsv`（476 行）；全证据：`EVIDENCE\ENTRY_ADJUDICATION_FULL.tsv`。
- 专表：`ALREADY_IN_COVERAGE.tsv`、`B_RAIL_C5_EXCLUDED.tsv`、`A_RAIL_DETAILS.tsv`。
- 审计原文：`P0_GATE\_audit\VERDICT.md` §四/§五。
- 复跑：`python P0_GATE\work\adjudicate_r10.py && python P0_GATE\work\verify.py && python P0_GATE\work\make_reports.py`。
- capstone 5.0.7 `skipdata=True`；不读 `vtables_v2.json`；不写 `COVERAGE\`。

## 交付路径
- `P0_GATE\ENTRY_ADJUDICATION.tsv`
- `P0_GATE\ADJUDICATION_SUMMARY.md`
- `P0_GATE\PROGRESS.md`
- `P0_GATE\EVIDENCE\`、`P0_GATE\work\`