Q1 | 可join: 是 ; 只在A=47/3,525,160B ; 只在旧=0/0B ; 被改写=5个
Q2 | 新增中: 自身产物=36/3,460,888B ; 可能真事实=11/64,272B ; 无法判定=0/0B
Q3 | 被改写分布: 5个(<200)，逐条见下方 Q3 逐条表
Q4 | 分解结果: 自身产物 X=37个文件/净+3,441,605B ; 树增长 Z=15个文件/净+95,965B ; 无法判定=0/0 ; 校验 3,441,605+95,965=3,537,570=3,525,160+12,410（两快照净差，逐字节闭合）；口径与局限见下方
Q5 | 正控: 法1=47(PowerShell Import-Csv / analyze.ps1) 法2=47(Python csv / control.py) | 一致（其余9项指标亦全一致）
OVERALL | F24 该写入本次两快照（11:55→12:31）的逐文件分解（它可核、逐字节闭合），但不得拿它充当历史漂移 24,623→24,693 的分解；且必须同时写明三项局限：selfkind 未审计、7/47 个新增文件的 mtime 早于旧快照落盘时刻、真事实/自身产物属语义判据。

---

## 0 · 数字溯源（纪律 1：每个数字给「源文件 + 列名 + 脚本名」）

| 数字 | 源文件 | 列名 | 脚本 |
|---|---|---|---|
| 24,676 行 / 1,586,426,788 B（旧快照） | `R17_R70_T1_REPRO\files_scale_today.tsv` | rel / bytes | analyze.ps1、control.py |
| 24,723 行 / 1,589,964,358 B（新快照） | `R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv` | rel / bytes | analyze.ps1、control.py |
| 只在A=47 / 3,525,160 B | 两表按 rel join | rel、bytes | analyze.ps1、control.py |
| 只在旧=0 / 0 B | 两表按 rel join | rel、bytes | analyze.ps1、control.py |
| 被改写=5，delta=+12,410 B | 两表按 rel join | bytes | analyze.ps1、control.py |
| 自身产物新增=36 / 3,460,888 B | `q1_onlyA.tsv`（源自上面两表） | selfkind / rel / bytes | classify.ps1 |
| 可能真事实新增=11 / 64,272 B | `q1_onlyA.tsv` | selfkind / rel / bytes | classify.ps1 |
| 改写中自身产物=1 / -19,283 B | `q1_changed.tsv` | selfkind / delta | classify.ps1 |
| 改写中真事实=4 / +31,693 B | `q1_changed.tsv` | rel / delta | classify.ps1 |
| Q5 双实现 47 vs 47 | 两张源 TSV（直读，不经中间文件） | rel | analyze.ps1 vs control.py |

逐文件证据产物（均在 `R17_R75_T2_DRIFT\`）：`summary.tsv`、`q1_onlyA.tsv`、`q1_onlyOld.tsv`、`q1_changed.tsv`、`q2_classification.tsv`、`q3_classification.tsv`、`q2q3q4_summary.tsv`；脚本 `analyze.ps1`、`classify.ps1`、`control.py`。**未运行 `mev675.py`**（只读，未执行该目录下任何脚本）。

---

## Q1 · 可 join 证明与比对结果

- 两表结构：`files_scale_today.tsv` = `rel / ext / bytes / mtime_ns`；`files_tier_A_snap2.tsv` = `rel / ext / bytes / mtime_ns / selfkind`。共有可比列 `rel / ext / bytes / mtime_ns`，`rel` 均为相对 `lead\` 根的路径（首段 263 个顶层目录，两表一致）。
- 键唯一性：旧表 24,676 行 = 24,676 个不同 rel；新表 24,723 行 = 24,723 个不同 rel；两表均无重复 rel 分组。
- 交集 24,676 个 rel 中，24,652 个 mtime_ns 完全相同、24,671 个 bytes 完全相同 ⇒ 确系同一命名空间、同一棵树的两次快照。
- 只在A=47 个 / 3,525,160 B；只在旧=0 个 / 0 B；两边都有但 bytes 变了=5 个（旧字节合计 5,820,379，新字节合计 5,832,789，净 +12,410 B）。
- 逐字节闭合：1,586,426,788 + 3,525,160 + 12,410 = 1,589,964,358，与两表 bytes 总和之差精确相等。

## Q2 · 47 个新增文件的分类（口径与规则）

按 `files_tier_A_snap2.tsv` 的 `selfkind` 列优先，空值再按文件名形态判；规则逐条写在 `q2_classification.tsv` 的 `rule` 列：

| 规则 | 个数 | 字节 | 归类 |
|---|---|---|---|
| `selfkind=C3_r35_r39_dir` | 8 | 40,562 | 自身产物 |
| `selfkind=C3_r35_r39_dir+C5_report_md` | 1 | 1,591 | 自身产物 |
| `selfkind=C5_report_md` | 1 | 33,765 | 自身产物 |
| `selfkind=C6_out_txt` | 1 | 1,002 | 自身产物 |
| `selfkind=C7_s_rerun` | 3 | 376,115 | 自身产物 |
| `selfkind=C8_files_scale` | 1 | 2,308,725 | 自身产物 |
| `selfkind=C9_scale_json` | 2 | 1,649 | 自身产物 |
| filename-pattern（*.log、*.before_*.md、SUPERSEDED.md、*_probe.json、*_check.txt、*_strings.txt、FACT_INDEX.tsv） | 19 | 697,479 | 自身产物 |
| doc-pattern（_cards/R40-*.md、REPORT.md、CHANGES.md、README.md） | 11 | 64,272 | 可能真事实 |
| 无法判定 | 0 | 0 | — |

selfkind 命中 17 个 / 2,763,409 B；文件名判据补出 19 个 / 697,479 B（多为日志、滚动备份、scale/probe 输出，与 §2.28 三表的自身产物口径同族）。

## Q3 · 被改写 5 个逐条（全 <200，故逐条列）

| 路径 | 旧字节 | 新字节 | delta | 归类 / 依据 |
|---|---|---|---|---|
| `GOAL_THREE_TARGETS_20261018.md` | 4,471,210 | 4,482,041 | +10,831 | 事实文档：滚动台账（rel 命中台账文件名） |
| `next_re_20261117_r14/BOARD_ARCHIVE.md` | 449,174 | 462,184 | +13,010 | 事实文档：看板归档 |
| `next_re_20261117_r14/R14_COMMON.md` | 301,890 | 311,946 | +10,056 | 事实文档：事实底座 |
| `next_re_20261117_r14/R17_R70_T5_DETOUR/detour_profile_out.txt` | 552,729 | 533,446 | -19,283 | 自身产物：selfkind=C6_out_txt |
| `next_re_20261117_r14/STATUS_BOARD.md` | 45,376 | 43,172 | -2,204 | 事实文档：状态看板 |

自身产物改写 1 个 / 净 -19,283 B；事实文档改写 4 个 / 净 +31,693 B；无法判定 0。

## Q4 · 可核分解与其口径 / 局限

**分解（两快照净差 +47 文件 / +3,537,570 B）：**

| 类 | 新增 | 新增字节 | 改写 | 改写净字节 | 合计文件 | 净字节 |
|---|---|---|---|---|---|---|
| 自身产物 | 36 | 3,460,888 | 1 | -19,283 | 37 | +3,441,605 |
| 树增长（可能真事实） | 11 | 64,272 | 4 | +31,693 | 15 | +95,965 |
| 无法判定 | 0 | 0 | 0 | 0 | 0 | 0 |

**口径：** ① 比对单位是 rel 键（路径），不是目录、不是尺寸估算；② "新增/消失/被改写"分别定义为「只在 A」「只在旧」「两边都有且 bytes 不等」，字节数取各自快照的 bytes 列；③ 新快照的 selfkind 列优先于文件名判据；④ 改写项按 delta=new-old 记净字节；⑤ 分解只覆盖这两张清单之间的差，不覆盖清单之外的任何时刻。

**局限（必须随分解一起引用）：**
1. **selfkind 未审计**：§2.28「未取得③」明示档 C 的判据「尚未经第二人审计」，且「其它回滚副本 384 个 / 258,794,083 B」未计入档 C ⇒ 本分解中按 selfkind/filename 归入自身产物的 36 个，是沿用未审计口径，不是独立证明。
2. **7/47 个新增文件的 mtime 早于旧快照落盘时刻**（旧快照文件 mtime=2026-11-22T03:55:10Z）：`_run_judge.log`、`_run_repro.log`、`_run_scale.log`、`_run_search.log`、`s_rerun_buckets675.tsv`、`s_rerun_judge_primary.json`、`s_rerun_recheck116.tsv` 的 mtime 在 03:53:35–03:54:50Z。故"只在A"是 join 层面的差，不等于"在该 36 分钟窗口内新建"；旧扫描很可能先于这些文件写入就走过了该目录（§2.26 记同一命令曾在数分钟内从 24,650 漂到 24,691）。
3. **24 个共有 rel 的 mtime_ns 变了但 bytes 未变**（analyze.ps1 实测 same_mtime_ns=24,652 / diff=24）：按卡定义不算"被改写"，但它们是被触碰/同长重写过的，说明 bytes 单判据会漏记内容变动。
4. **真事实/自身产物是语义判据**：全部 11 个"可能真事实"都是 REPORT.md、_cards/*.md、CHANGES.md、README.md，即测量流程自己写出的文档；卡定义明确把"新 RE 卡的 EVIDENCE/REPORT"列为"可能的真事实"，故归入该栏，但这是判读而非可核事实。且 selfkind 口径不自洽：`AUDIT_REPORT.md` 命中 `C5_report_md` 算自身产物，裸 `REPORT.md` 却是空 selfkind（45,268 B 未计入自身产物）。
5. **无中间快照**：窗口内"建了又删"的文件不可见；无法把 36 分钟内的写入时序排开。
6. **与历史漂移不可互换**：§2.27 的「41 文件 / 3,483,644 B，其中 24 文件 / 1,838,770 B 无从归因」是另两档快照的差，不能由本分解替代；本分解只解释 11:55→12:31 这一对（其净差仅 +47 / +3,537,570 B）。

**要做出更强分解需要什么：** 同一扫描器在两次快照都写 selfkind 列（并对 REPORT/card 族给出裁决）、带目录遍历时刻的逐文件清单、以及一个中间快照；否则只能得到本次这种"join 级 + 语义判据"的分解。

## 未取得

- 未取得两张快照同一时刻的 selfkind 一致性校验（旧表无 selfkind 列）。
- 未取得窗口内写入时序（无中间快照）。
- 未取得被改写 5 个文件的内容级 diff（两表只有 bytes / mtime_ns，无内容快照）。
- 未对 selfkind 判据做第二人审计（沿用 §2.28 未审计口径）。

## 未触碰证明

R16_MEASURE_EVID675 三文件，开工与收工各列一次（mtime 为 UTC，TICKS 为 LastWriteTimeUtc.Ticks）：

| 文件 | 时刻 | 字节 | mtime (UTC) | TICKS |
|---|---|---|---|---|
| `buckets675.tsv` | 开工 | 301,579 | 2026-11-22T03:54:50.5759137Z | 639309164905759137 |
| `buckets675.tsv` | 收工 | 301,579 | 2026-11-22T03:54:50.5759137Z | 639309164905759137 |
| `recheck116.tsv` | 开工 | 53,790 | 2026-11-22T03:54:50.5836343Z | 639309164905836343 |
| `recheck116.tsv` | 收工 | 53,790 | 2026-11-22T03:54:50.5836343Z | 639309164905836343 |
| `_judge_primary.json` | 开工 | 20,746 | 2026-11-22T03:54:50.5908398Z | 639309164905908398 |
| `_judge_primary.json` | 收工 | 20,746 | 2026-11-22T03:54:50.5908398Z | 639309164905908398 |

三文件开工/收工的字节数与 TICKS 逐一相同 ⇒ 未触碰。未运行 `mev675.py`；`lead\` 下仅写入 `next_re_20261117_r14\R17_R75_T2_DRIFT\`。
