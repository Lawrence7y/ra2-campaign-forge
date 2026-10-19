# W3-RPT1 派工单 · **M35R 的 9 条未证读取点补证（§13 门禁读取点第二轮）**（Qoder CN · 新会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：M35R（已验收，`[100% ALL PASS]`）的诚实遗留：
> > `read-point: ATTESTED=27 PARTIAL=5 UNATTESTED=4 (of 36)` —— **9 条读取点未完全证实**（PARTIAL 5 + UNATTESTED 4）。
> **对象 = 任务 E 的 §13 前身卡 M35 的 36 条门禁字段账**（`zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_va_manifest.json`，只读）与其门禁读取逻辑。
> **目标**：把 9 条从 `PARTIAL/UNATTESTED` 推到 `ATTESTED` 或**给出"为何不可证"的结构化结论**。

## 🔴 铁律（先读）
1. **只读**：`m35_ch13_expand/**`、`zcode_live/W3_20261002/m35r_ch13_audit/**`（M35R 原件）、`ra2youli/game.exe`、`gamemd.exe`、`docs/**`、原版侧 ATLAS。
2. **读取点的定义**：每个门禁字段（PE 头/节表/红线段头）在**门禁文档或工具代码**里对应"哪段逻辑读它、用来判什么" —— **补证 = 找到那处读取逻辑的 file:line + 逐字复述其判据**，或用 `tools/` 里真实工具对该字段做一次**触发性实测**（改临时副本的该字段 ⇒ 工具必须报错/变判 —— 这是最强补证）。
3. **触发性实测只在临时副本上做**（拷贝 `game.exe` 到本写域改，**真件零写入**；实测后副本保留作证据）。
4. **拿不准 ⇒ 保持原判 + 结构化说明**（`STILL_UNPROVEN` + 卡在哪一步 + 需要什么才能证），**禁止把 PARTIAL 硬升 ATTESTED**。
5. **空扫描报 `INSTRUMENT_FAILED`**；**写域仅此**：`out/re_work/qc/W3_20261002/rpt1_readpoints/`

## 做什么（四件）
1. **9 条清单化**：从 M35R 的 `read-point` 结果文件里抽出 5+4 条，逐条列 `VA/字段名/当时为何未证`。
2. **逐条补证**（按铁律 2 的两条路径，优先触发性实测）。
3. **汇总表**：`ATTESTED_N / STILL_UNPROVEN_M`，每条带证据（file:line 或实验读数）。
4. **反向验证**：抽 1 条你判 ATTESTED 的，**故意用错误字段值重跑触发实验 ⇒ 必须 FAIL**（证明触发器真在验这个字段）。

## 交付
`RPT1_REPORT.md`（§A 十节骨架；`[0]` 直答）· `readpoint_recheck.json`（9 条逐条）· `trigger_experiments/`（临时副本 + 实验原文）· `verify_rpt1.py`（**EXIT=0 + `verdict tally` 行**）

## 回报 `[0]`
① 9 条清单 ② ATTESTED/STILL_UNPROVEN 计数 ③ 触发实验最强证据一例 ④ 反向验证 ⑤ `verdict tally` 原文

## 底线
> **宁可交"9 条补上 5 条、4 条 STILL_UNPROVEN 并说明缺什么"，也不要交"9/9 全 ATTESTED"—— M35R 当初诚实留白，别用升格把它抹掉。**
