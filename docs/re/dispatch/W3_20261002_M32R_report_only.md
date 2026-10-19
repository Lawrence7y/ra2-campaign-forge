# W3-M32R-RPT 派工单 · M32R 收尾报告补写（第 4 次催办，改派新会话）

> 派发：2026-10-02 19:5x（Lead）· 执行：WorkBuddy（**新会话** —— 原 M32R 会话三次催办未回，疑已失联）
> 预估 30–45 分钟 · 这是**纯收尾件**：门禁早已 GATE OK，只欠报告

## 背景

M32R（RTTI/BCA 复核）核心交付已齐且验证器早已通过：
- `out/re_work/workbuddy/W3_20261002/m32r_rtti_bca/`：`m32r_recheck.json`（16,280 B）、`correction_table.md`、step01–04 脚本、`verify_m32r.py`（自证直接从 game.exe 重读字节交叉校验，A–G 七门）
- **缺的只有一件：`M32R_REPORT.md`**（Lead 已三次留条催办：`_LEAD_WRAPUP.md`、`_LEAD_FINAL_REPORT_ONLY.md`）

## 任务

1. 读派工单 `docs/re/dispatch/W3_20261002_M32R_rtti_bca_recheck.md` + 全部既有产物（**全部只读**），写出 `M32R_REPORT.md`：
   - 按派工单的回报结构逐项落：结论、verdict tally、更正表（correction_table.md 的要点收进报告）、负控/反向验证、只读纪律自证；
   - **所有数字必须从 m32r_recheck.json / raw / correction_table.md 现读现抄**，逐条标来源键名；**一个数都不许自己重算或凭记忆写**；
   - 原会话若在 `_LEAD_*.md` 留有要求，逐条回应（含"没做就是没做"的诚实项）。
2. 亲跑 `verify_m32r.py` ⇒ 必须 EXIT=0（报告缺失时它本就该红/或报告是其断言对象之一 —— 跑之前先读它的报告相关断言，确保你的报告满足其口径）。
3. **负控**：把报告里你抄的一个关键读数在副本里改坏 ⇒ 相关交叉校验思路必须能抓到（若 verify_m32r 不校验报告文本，则改为：人工对照该键在 json 与报告中的一致性表，逐键 PASS/FAIL 列出）。

## 铁律

- **写域仅** `out/re_work/workbuddy/W3_20261002/m32r_rtti_bca/M32R_REPORT.md`（+ 可在 `out/re_work/workbuddy/W3_20261002/m32r_rpt/` 放你的留证/对照表）。
- 该目录其余文件、game.exe、ATLAS、dispatch 台账**零写入**；**不许改 verify_m32r.py 与既有产物**。
- 空扫描 = INSTRUMENT_FAILED；拿不准的项如实列"原会话未留档、无从取证"，**禁止编造**。

## 交付

`M32R_REPORT.md` + `m32r_rpt/` 下的一致性对照表。完成后回报 `[0]`：报告结构目录 + verify_m32r EXIT + verdict tally 原文 + 你无法取证而如实留白的清单。
